"""
Thesis figures (static, 300 dpi PNG).
Usage: python make_figures.py <phase3_review_features.csv> <processed_reviews_all.csv> <out_dir>
Colour = accommodation type, fixed everywhere: Ryokan indigo, Hotel vermilion, Hybrid gold (Kyoto palette)
(validated colour-blind safe as a 3-slot set). Star ratings use a red-grey-blue diverging scale.
Sentiment is VADER, the primary measure of the thesis. Proportions carry Wilson 95% intervals; regression coefficients carry HC3 95% intervals.
"""
import os, sys, warnings
import numpy as np, pandas as pd, matplotlib as mpl
mpl.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
import statsmodels.formula.api as smf, statsmodels.api as sm
from statsmodels.stats.proportion import proportion_confint
from sklearn.feature_extraction.text import CountVectorizer, ENGLISH_STOP_WORDS
warnings.filterwarnings("ignore")

FEAT, RAW, OUTD = sys.argv[1], sys.argv[2], sys.argv[3]
os.makedirs(OUTD, exist_ok=True)
INK, INK2, MUTED, GRID, AXIS, BAND = "#22201c", "#57524a", "#8a8375", "#e9e4d8", "#bdb6a6", "#f4f1e8"
COL = {"Ryokan": "#1f6fa8", "Hotel": "#d9452b", "Hybrid": "#c9a227"}  # Kyoto: indigo, vermilion, gold
TIERS = ["Ryokan", "Hybrid", "Hotel"]
STAR = {1: "#9c2a17", 2: "#d9452b", 3: "#efa390", 4: "#9fc0d8", 5: "#1f6fa8"}
NAME = {"Four Seasons Hotl Kyoto": "Four Seasons Kyoto", "Parkhyatt": "Park Hyatt Kyoto",
        "Hyatt Regency Kyoto": "Hyatt Regency Kyoto", "Junei Hotel Kyoto": "The Junei Hotel",
        "Kyokoyado Muromachi Yutone": "Muromachi Yutone", "Nishiyama Ryokan": "Nishiyama Ryokan",
        "Ryokufuso": "Ryokufuso", "Shiraume": "Shiraume", "Nazuna Kyoto Gosho": "Nazuna Gosho",
        "Nazuna Kyoto Nijojo": "Nazuna Nijo-jo"}
A = ["dining", "bath", "room", "staff_service", "location", "value_price", "culture"]
AL = {"dining": "Dining", "bath": "Bath", "room": "Room", "staff_service": "Staff & service",
      "location": "Location", "value_price": "Value & price", "culture": "Culture"}
mpl.rcParams.update({
    "font.family": ["Liberation Serif", "DejaVu Sans"], "font.size": 9.5, "axes.edgecolor": AXIS, "axes.linewidth": 0.8,
    "axes.labelcolor": INK2, "axes.labelsize": 9.5, "xtick.color": MUTED, "ytick.color": MUTED,
    "xtick.labelcolor": INK2, "ytick.labelcolor": INK2, "xtick.major.size": 0, "ytick.major.size": 0,
    "axes.spines.top": False, "axes.spines.right": False, "axes.grid": True, "grid.color": GRID,
    "grid.linewidth": 0.6, "grid.linestyle": "-", "axes.axisbelow": True, "figure.facecolor": "white",
    "axes.facecolor": "white", "savefig.dpi": 300, "text.color": INK, "legend.frameon": False,
    "legend.fontsize": 9, "axes.titlesize": 10.5, "axes.titleweight": "bold", "axes.titlelocation": "left",
    "axes.titlecolor": INK, "axes.titlepad": 10})

d = pd.read_csv(FEAT)
d["name"] = d.prop.map(NAME)
d["log_words"] = np.log(d.n_words.clip(lower=1))
d["low"] = (d.Rating <= 3).astype(int)
core = d[d.tier.isin(["Ryokan", "Hotel"])].copy()

def save(fig, name):
    fig.savefig(os.path.join(OUTD, name + ".png"), bbox_inches="tight", pad_inches=0.08)
    plt.close(fig)

def tier_legend(ax, tiers=TIERS, loc="lower right", **k):
    ax.legend(handles=[Patch(color=COL[t], label=t) for t in tiers], loc=loc, handlelength=1, handleheight=0.8, **k)

# ------------------------------------------------------------------ Fig 1 dataset overview
fig, (a1, a2) = plt.subplots(1, 2, figsize=(7.4, 3.3), gridspec_kw={"width_ratios": [1, 1.15], "wspace": 0.55})
cnt = d.groupby(["name", "tier"]).size().reset_index(name="n").sort_values("n")
a1.barh(cnt.name, cnt.n, color=[COL[t] for t in cnt.tier], height=0.62)
for y, n in enumerate(cnt.n):
    a1.text(n + 40, y, f"{n:,}", va="center", fontsize=8.3, color=INK2)
a1.set_xlim(0, cnt.n.max() * 1.18); a1.grid(axis="y", visible=False); a1.set_xlabel("Number of reviews")
a1.set_title("(a) Reviews per property"); tier_legend(a1)
yr = d[d.Year <= 2025].groupby(["Year", "tier"]).size().unstack(fill_value=0)
ymax = yr.values.max() * 1.12
a2.axvspan(2019.5, 2022.5, color=BAND, zorder=0, lw=0)
a2.text(2021, ymax * 0.93, "COVID-19", ha="center", color=MUTED, fontsize=8.3)
for t in ["Hotel", "Ryokan", "Hybrid"]:
    a2.plot(yr.index, yr[t], color=COL[t], lw=2, solid_capstyle="round", solid_joinstyle="round")
    a2.text(2025.4, yr[t].iloc[-1], t, va="center", fontsize=8.3, color=INK2)
a2.set_ylim(0, ymax); a2.set_xlim(2005, 2027.5); a2.set_xticks(range(2006, 2026, 4))
a2.set_ylabel("Reviews per year"); a2.set_title("(b) Reviews per year (2026 partial, omitted)")
a2.grid(axis="x", visible=False)
save(fig, "fig01_dataset_overview")

# ------------------------------------------------------------------ Fig 2 rating distribution (diverging stacked bars)
sh = pd.crosstab(d.name, d.Rating, normalize="index").reindex(columns=[1, 2, 3, 4, 5], fill_value=0)
st = d.groupby(["name", "tier"]).agg(mean=("Rating", "mean"), low=("low", "mean"), n=("Rating", "size")).reset_index()
rows, ypos, y, heads = [], [], 0, []
for t in reversed(TIERS):  # Ryokan ends on top, Hotel at the bottom
    sub = st[st.tier == t].sort_values("low", ascending=False)
    for _, r in sub.iterrows():
        rows.append(r); ypos.append(y); y += 1
    heads.append((y - 1 + 0.78, t))
    y += 1.0
fig, ax = plt.subplots(figsize=(7.4, 4.3))
for r, yy in zip(rows, ypos):
    v = sh.loc[r["name"]]
    k = dict(height=0.64, edgecolor="white", linewidth=0.8)
    ax.barh(yy, -v[3], color=STAR[3], **k); ax.barh(yy, -v[2], left=-v[3], color=STAR[2], **k)
    ax.barh(yy, -v[1], left=-v[3] - v[2], color=STAR[1], **k)
    ax.barh(yy, v[4], color=STAR[4], **k); ax.barh(yy, v[5], left=v[4], color=STAR[5], **k)
    ax.text(-r["low"] - 0.012, yy, f"{r['low']:.0%}", ha="right", va="center", fontsize=9.3, color=INK2)
    ax.text(v[4] + v[5] / 2, yy, f"{v[5]:.0%}", ha="center", va="center", fontsize=9.3, color="white")
for hy, t in heads:
    ax.text(-0.2, hy, t.upper(), ha="left", va="center", fontsize=8.8, color=MUTED, fontweight="bold")
ax.axvline(0, color=INK, lw=0.9)
ax.set_ylim(-0.6, max(ypos) + 1.2); ax.set_yticks(ypos); ax.set_yticklabels([f"{r['name']}  (n = {int(r['n']):,})" for r in rows])
ax.set_xlim(-0.2, 1.0); ax.set_xticks([-0.2, 0, 0.2, 0.4, 0.6, 0.8, 1.0])
ax.set_xticklabels(["20%", "0", "20%", "40%", "60%", "80%", "100%"])
ax.set_xlabel("← three stars or fewer          Share of reviews          four and five stars →")
ax.grid(axis="y", visible=False); ax.spines["left"].set_visible(False)
ax.legend(handles=[Patch(color=STAR[s], label=f"{s}★") for s in [1, 2, 3, 4, 5]], ncol=5,
          loc="lower left", bbox_to_anchor=(0.1, 1.0), handlelength=1, handleheight=0.8, columnspacing=1.2)
save(fig, "fig02_rating_distribution")

# ------------------------------------------------------------------ Fig 3 review sentiment by property and type
from scipy.stats import gaussian_kde
fig, (a1, a2) = plt.subplots(1, 2, figsize=(7.6, 3.9), gridspec_kw={"width_ratios": [1.5, 1], "wspace": 0.3})
med = d.groupby(["name", "tier"]).s_mean.median().reset_index().sort_values("s_mean", ascending=False)
rng = np.random.RandomState(1)
for i, r in enumerate(med.itertuples()):
    v = d.loc[d.name == r.name, "s_mean"].dropna().values
    sub = v if len(v) <= 220 else rng.choice(v, 220, replace=False)
    a1.scatter(i + rng.uniform(-0.28, 0.28, len(sub)), sub, s=5, color=COL[r.tier], alpha=0.55, linewidths=0, zorder=2)
    a1.boxplot([v], positions=[i], widths=0.7, showfliers=False, patch_artist=True,
               boxprops=dict(facecolor="none", edgecolor=INK, linewidth=0.9), medianprops=dict(color=INK, linewidth=1.8),
               whiskerprops=dict(color=INK, linewidth=0.9), capprops=dict(linewidth=0), zorder=3)
a1.set_xticks(range(len(med))); a1.set_xticklabels([n.replace(" Kyoto", "").replace(" Ryokan", "").replace("The ", "") for n in med.name],
                                                   rotation=40, ha="right", rotation_mode="anchor")
a1.set_xlim(-0.6, len(med) - 0.4); a1.set_ylim(-0.45, 1.0); a1.axhline(0, color=AXIS, lw=0.8)
a1.set_ylabel("Review sentiment (VADER)"); a1.grid(axis="x", visible=False); a1.set_title("(a) By property")
xs = np.linspace(-0.45, 1.0, 400)
for t in ["Hotel", "Hybrid", "Ryokan"]:
    dens = gaussian_kde(d.loc[d.tier == t, "s_mean"].dropna().values)(xs)
    a2.fill_between(xs, dens, color=COL[t], alpha=0.22, lw=0, zorder=2); a2.plot(xs, dens, color=COL[t], lw=1.8, zorder=3)
a2.set_xlim(-0.45, 1.0); a2.set_ylim(0); a2.set_xlabel("Review sentiment (VADER)"); a2.set_ylabel("Density")
a2.set_title("(b) By accommodation type"); a2.grid(axis="x", visible=False)
a2.legend(handles=[Patch(color=COL[t], label=t) for t in TIERS], loc="upper left", handlelength=1, handleheight=0.8)
save(fig, "fig03_sentiment_by_property")

# ------------------------------------------------------------------ Fig 4 low-box and recommend (dots with Wilson 95% intervals)
agg = d.groupby(["name", "tier"]).agg(low=("low", "mean"), rec=("rec", "mean"), n=("Rating", "size")).reset_index()
fig, axs = plt.subplots(1, 2, figsize=(7.4, 3.5), gridspec_kw={"wspace": 0.75})
for ax, col, ttl in [(axs[0], "low", "(a) Share of reviews rated ≤3★"), (axs[1], "rec", "(b) Share of reviews recommending")]:
    s = agg.sort_values(col); top = 0
    for i, r in enumerate(s.itertuples()):
        v = getattr(r, col); lo, hi = proportion_confint(round(v * r.n), r.n, method="wilson"); top = max(top, hi)
        ax.plot([lo, hi], [i, i], color=COL[r.tier], lw=2, solid_capstyle="round", alpha=0.45)
        ax.scatter(v, i, s=42, color=COL[r.tier], edgecolor="white", linewidth=1.5, zorder=3)
        ax.text(hi + agg[col].max() * 0.04, i, f"{v:.0%}" if v >= 0.01 else f"{v:.1%}", va="center", fontsize=8.6, color=INK2)
    ax.set_yticks(range(len(s))); ax.set_yticklabels(s.name); ax.set_title(ttl)
    ax.set_xlim(0, top * 1.18); ax.xaxis.set_major_formatter(mpl.ticker.PercentFormatter(1.0, decimals=0))
    ax.grid(axis="y", visible=False)
tier_legend(axs[0], loc="lower right")
save(fig, "fig04_lowbox_recommend")

# ------------------------------------------------------------------ Fig 5 distinctive vocabulary
raw = pd.read_csv(RAW)
TIERMAP = dict(zip(d.prop, d.tier))
raw["tier"] = raw.Hotel_Name.map(TIERMAP)
rc_ = raw[raw.tier.isin(["Ryokan", "Hotel"])]
STOPK = set(ENGLISH_STOP_WORDS) | {"kyoto", "japan", "japanese", "hotel", "hotels", "ryokan", "ryokans", "inn", "stay", "stayed", "staying"}
cvk = CountVectorizer(token_pattern=r"(?u)\b[a-z][a-z]+\b", ngram_range=(1, 2), min_df=25, stop_words=list(STOPK))
Xb = (cvk.fit_transform(rc_.Text.astype(str)) > 0).astype(int)
voc = np.array(cvk.get_feature_names_out()); props = rc_.Hotel_Name.values
rates = pd.DataFrame({p: np.asarray(Xb[props == p].mean(0)).ravel() for p in np.unique(props)}, index=voc)
rates = rates[(rates.max(1) / rates.sum(1)) <= 0.5]
rcols = [c for c in rates if TIERMAP[c] == "Ryokan"]; hcols = [c for c in rates if TIERMAP[c] == "Hotel"]
kt = pd.DataFrame({"r": rates[rcols].mean(1), "h": rates[hcols].mean(1)})
kt["lr"] = np.log2((kt.r + 1e-3) / (kt.h + 1e-3))
sepR = rates[rcols].min(1) > rates[hcols].max(1); sepH = rates[rcols].max(1) < rates[hcols].min(1)
# keep single words and bigrams that are not just a repeat of an already-listed word
def pick(df, n):
    out = []
    for term in df.index:
        if any(w in term.split() or term in w.split() for w in out):
            continue
        out.append(term)
        if len(out) == n: break
    return df.loc[out]
topR = pick(kt[sepR].sort_values("lr", ascending=False), 12)
topH = pick(kt[sepH].sort_values("lr"), 12)
fig, ax = plt.subplots(figsize=(6.6, 5.0))
labs = list(topH.index[::-1]) + list(topR.index[::-1])
vals = list(topH.lr[::-1]) + list(topR.lr[::-1])
cols = [COL["Hotel"]] * len(topH) + [COL["Ryokan"]] * len(topR)
ax.barh(range(len(vals)), vals, color=cols, height=0.62)
pc = lambda x: f"{x * 100:.0f}%" if x >= 0.0995 else f"{x * 100:.1f}%"
for i, (v, l) in enumerate(zip(vals, labs)):
    lab = f"{l}  ({pc(kt.r[l])} | {pc(kt.h[l])})"
    ax.text(v + (0.15 if v > 0 else -0.15), i, lab, va="center", ha="left" if v > 0 else "right", fontsize=8.3, color=INK)
ax.axvline(0, color=AXIS, lw=0.8); ax.set_yticks([]); ax.spines["left"].set_visible(False)
lo_, hi_ = np.floor(min(vals)) - 5.4, np.ceil(max(vals)) + 6.6  # room for the term labels
ax.set_xlim(lo_, hi_)
ticks = [t for t in range(-8, 9, 2)]
ax.set_xticks(ticks); ax.set_xticklabels(["1×" if t == 0 else f"{2**abs(t):g}×" for t in ticks])
ax.set_xlabel("How many times more often the term appears (logarithmic scale)")
ax.text(lo_ + 0.1, len(vals) - 0.3, "← More frequent in Hotel reviews", fontsize=8.3, color=INK2)
ax.text(hi_ - 0.1, len(vals) - 0.3, "More frequent in Ryokan reviews →", fontsize=8.3, color=INK2, ha="right")
ax.grid(axis="y", visible=False)
save(fig, "fig05_distinctive_vocabulary")

# ------------------------------------------------------------------ Fig 6 aspect salience and negative share
def tier_mean(df, col):
    pm = df.groupby(["prop", "tier"])[col].mean().reset_index()
    return pm.groupby("tier")[col].mean()
sal = pd.DataFrame({a: tier_mean(core, "mention_" + a) for a in A}).T
neg = pd.DataFrame({a: tier_mean(core[core["mention_" + a] == 1], "neg_" + a) for a in A}).T
fig, axs = plt.subplots(1, 2, figsize=(7.4, 3.9), gridspec_kw={"wspace": 0.45})
order = (sal.Ryokan - sal.Hotel).sort_values().index
for ax, tab, ttl, fmt in [(axs[0], sal, "(a) Share of reviews mentioning the aspect", 0),
                          (axs[1], neg, "(b) Share of mentions that are negative", 0)]:
    tab = tab.loc[order]
    for i, a in enumerate(tab.index):
        ax.plot([tab.Hotel[a], tab.Ryokan[a]], [i, i], color=AXIS, lw=2, solid_capstyle="round", zorder=1)
        src = core if ax is axs[0] else core[core["mention_" + a] == 1]
        pv = src.groupby(["prop", "tier"])[("mention_" if ax is axs[0] else "neg_") + a].mean().reset_index()
        for t, dy in [("Hotel", -0.24), ("Ryokan", 0.24)]:
            ax.scatter(pv.loc[pv.tier == t].iloc[:, 2], [i + dy] * int((pv.tier == t).sum()), s=11, color=COL[t], alpha=0.55, linewidths=0, zorder=2)
            ax.scatter(tab[t][a], i, s=46, color=COL[t], edgecolor="white", linewidth=1.5, zorder=3)
    ax.set_yticks(range(len(tab))); ax.set_yticklabels([AL[a] for a in tab.index]); ax.set_title(ttl)
    ax.xaxis.set_major_formatter(mpl.ticker.PercentFormatter(1.0, decimals=0)); ax.grid(axis="y", visible=False)
axs[0].set_xlim(0, 1); axs[1].set_xlim(0, 0.2)
axs[1].xaxis.set_major_locator(mpl.ticker.MultipleLocator(0.05))
tier_legend(axs[1], tiers=["Ryokan", "Hotel"], loc="upper right")

save(fig, "fig06_aspect_profile")

# ------------------------------------------------------------------ Fig 7 penalty-reward
f6 = "Rating ~ " + " + ".join([f"pos_{a} + neg_{a}" for a in A]) + " + log_words + C(prop)"
res = {}
for t in ["Ryokan", "Hotel"]:
    m = smf.ols(f6, data=core[core.tier == t]).fit(cov_type="HC3")
    ci_ = m.conf_int()
    res[t] = pd.DataFrame({"reward": [m.params[f"pos_{a}"] for a in A], "p_r": [m.pvalues[f"pos_{a}"] for a in A],
                           "penalty": [m.params[f"neg_{a}"] for a in A], "p_p": [m.pvalues[f"neg_{a}"] for a in A],
                           "reward_lo": [ci_.loc[f"pos_{a}", 0] for a in A], "reward_hi": [ci_.loc[f"pos_{a}", 1] for a in A],
                           "penalty_lo": [ci_.loc[f"neg_{a}", 0] for a in A], "penalty_hi": [ci_.loc[f"neg_{a}", 1] for a in A],
                           "n_neg": [int(core[core.tier == t][f"neg_{a}"].sum()) for a in A]}, index=A)
order7 = (res["Hotel"].reward - res["Hotel"].penalty).sort_values().index
DARK = {"Ryokan": "#17466b", "Hotel": "#9c2a17"}  # darker step of each type's hue = penalty
fig, axs = plt.subplots(1, 2, figsize=(7.4, 3.9), sharex=True, gridspec_kw={"wspace": 0.08})
for ax, t in zip(axs, ["Ryokan", "Hotel"]):
    r = res[t].loc[order7]
    for i, a in enumerate(r.index):
        for col, pc, off, colr in [("reward", "p_r", 0.18, COL[t]), ("penalty", "p_p", -0.18, DARK[t])]:
            v = r[col][a]; sig = r[pc][a] < 0.05
            ax.barh(i + off, v, color=colr, alpha=1.0 if sig else 0.28, height=0.32)
            ax.plot([r[col + "_lo"][a], r[col + "_hi"][a]], [i + off, i + off], color=INK, lw=0.9, solid_capstyle="butt", zorder=4)
    ax.axvline(0, color=AXIS, lw=0.8); ax.set_title(f"{'(a)' if t=='Ryokan' else '(b)'} {t}s")
    ax.set_yticks(range(len(r))); ax.grid(axis="y", visible=False)
    ax.set_yticklabels([AL[a] for a in r.index] if t == "Ryokan" else [])
    ax.legend(handles=[Patch(color=COL[t], label="Reward: positive mention"),
                       Patch(color=DARK[t], label="Penalty: negative mention")],
              loc="lower left", handlelength=1, handleheight=0.8, fontsize=7.8)
    ax.set_ylim(-1.85, len(r) - 0.45)
axs[0].set_xlim(-1.32, 0.48)
fig.supxlabel("Change in star rating, holding the property and the other aspects constant",
              fontsize=9.3, color=INK2, y=-0.04)
save(fig, "fig07_penalty_reward")

# ------------------------------------------------------------------ Fig 8 IPA
fig, axs = plt.subplots(1, 2, figsize=(7.4, 3.5), sharey=True, gridspec_kw={"wspace": 0.12})
OFF = {"Ryokan": {"location": (6, -9), "bath": (6, 4), "culture": (6, -2), "room": (7, -3), "staff_service": (-6, -10),
                  "dining": (-6, 5), "value_price": (6, 2)},
       "Hotel": {"location": (6, 2), "bath": (6, 2), "culture": (6, 2), "room": (6, -9), "staff_service": (-6, -10),
                 "dining": (6, 2), "value_price": (-7, -2)}}
for ax, t in zip(axs, ["Ryokan", "Hotel"]):
    sub = core[core.tier == t]; r = res[t]
    imp = r.reward.clip(lower=0) + (-r.penalty).clip(lower=0)
    perf = pd.Series({a: sub.loc[sub[f"mention_{a}"] == 1, f"pos_{a}"].mean() for a in A})
    ax.axvline(imp.mean(), color=AXIS, lw=0.8); ax.axhline(perf.mean(), color=AXIS, lw=0.8)
    ax.scatter(imp, perf, s=46, color=COL[t], edgecolor="white", linewidth=1.5, zorder=3)
    for a in A:
        dx, dy = OFF[t][a]
        ax.annotate(AL[a], (imp[a], perf[a]), xytext=(dx, dy), textcoords="offset points", fontsize=8,
                    color=INK, ha="left" if dx > 0 else "right")
    ax.set_xlim(-0.08, 1.15); ax.set_title(f"{'(a)' if t=='Ryokan' else '(b)'} {t}s")
    ax.set_xlabel("Importance (reward + |penalty|, stars)")
    for (x, y_, s, ha) in [(1.12, 0.955, "Keep up the good work", "right"), (1.12, 0.69, "Concentrate here", "right"),
                           (-0.05, 0.955, "Possible overkill", "left"), (-0.05, 0.69, "Low priority", "left")]:
        ax.text(x, y_, s, fontsize=7.6, color=MUTED, ha=ha)
axs[0].set_ylabel("Performance: share of mentions that are positive")
axs[0].set_ylim(0.68, 0.97); axs[0].yaxis.set_major_formatter(mpl.ticker.PercentFormatter(1.0, decimals=0))
save(fig, "fig08_ipa")

# ------------------------------------------------------------------ Fig 9 seasonality
mo = core.groupby(["tier", "Month"]).Rating.agg(["mean", "sem"]).reset_index()
fig, ax = plt.subplots(figsize=(6.8, 3.3))
for a_, b_ in [(2.5, 4.5), (9.5, 11.5)]:
    ax.axvspan(a_, b_, color=BAND, lw=0, zorder=0)
ax.text(3.5, 5.0, "Cherry blossom", ha="center", fontsize=7.8, color=MUTED, va="top")
ax.text(10.5, 5.0, "Autumn foliage", ha="center", fontsize=7.8, color=MUTED, va="top")
for t in ["Ryokan", "Hotel"]:
    s = mo[mo.tier == t]
    ax.fill_between(s.Month, s["mean"] - 1.96 * s["sem"], s["mean"] + 1.96 * s["sem"], color=COL[t], alpha=0.12, lw=0)
    ax.plot(s.Month, s["mean"], color=COL[t], lw=2, solid_capstyle="round", solid_joinstyle="round")
    ax.text(12.25, s["mean"].iloc[-1], t, va="center", fontsize=8.3, color=INK2)
ax.set_xticks(range(1, 13)); ax.set_xticklabels(["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]); ax.set_xlim(0.7, 13.4)
ax.set_ylim(4.3, 5.0); ax.set_ylabel("Mean star rating (95% CI)"); ax.set_xlabel("Month the review was posted")
ax.grid(axis="x", visible=False)
save(fig, "fig09_seasonality")

# ------------------------------------------------------------------ Fig 10 long-run trend
yt = core[core.Year <= 2025].groupby(["tier", "Year"]).Rating.agg(["mean", "size"]).reset_index()
yt = yt[yt["size"] >= 30]
fig, ax = plt.subplots(figsize=(6.4, 3.0))
ax.axvspan(2019.5, 2022.5, color=BAND, lw=0, zorder=0)
ax.text(2021, 5.0, "COVID-19", ha="center", fontsize=7.8, color=MUTED, va="top")
for t in ["Ryokan", "Hotel"]:
    s = yt[yt.tier == t].set_index("Year")["mean"].reindex(range(2005, 2026))  # NaN breaks the line at sparse years
    ax.plot(s.index, s.values, color=COL[t], lw=2, marker="o", ms=4.5, mec="white", mew=1, solid_capstyle="round")
    last = s.dropna()
    ax.text(last.index[-1] + 0.4, last.iloc[-1], t, va="center", fontsize=8.3, color=INK2)
ax.set_ylim(4.2, 5.02); ax.set_xlim(2006.5, 2026.8); ax.set_ylabel("Mean star rating")
ax.xaxis.set_major_locator(mpl.ticker.MultipleLocator(2)); ax.xaxis.set_major_formatter(mpl.ticker.FormatStrFormatter("%d"))
ax.set_xlabel("Year the review was posted (years with ≥30 reviews shown)"); ax.grid(axis="x", visible=False)
save(fig, "fig10_trend")

# ------------------------------------------------------------------ Fig 11 behaviour/memory forest plot
f9 = " + ".join([f"pos_{a} + neg_{a}" for a in A]) + " + C(Rating) + log_words + C(prop)"
fig, axs = plt.subplots(1, 2, figsize=(7.4, 3.2), sharey=True, gridspec_kw={"wspace": 0.1})
fo = None
for ax, col, ttl in [(axs[0], "rec", "(a) Recommends the property"), (axs[1], "mem", "(b) Uses memory words")]:
    m = smf.glm(f"{col} ~ {f9}", data=core, family=sm.families.Binomial()).fit(cov_type="HC0")
    ci = m.conf_int()
    t_ = pd.DataFrame({"or": np.exp([m.params[f"pos_{a}"] for a in A]),
                       "lo": np.exp([ci.loc[f"pos_{a}", 0] for a in A]),
                       "hi": np.exp([ci.loc[f"pos_{a}", 1] for a in A]),
                       "p": [m.pvalues[f"pos_{a}"] for a in A]}, index=A)
    if fo is None: fo = t_.sort_values("or").index
    t_ = t_.loc[fo]
    ax.axvline(1, color=AXIS, lw=0.8)
    for i, a in enumerate(t_.index):
        sig = t_.p[a] < 0.05
        ax.plot([t_.lo[a], t_.hi[a]], [i, i], color=INK2, lw=2, alpha=1 if sig else 0.35, solid_capstyle="round")
        ax.scatter(t_["or"][a], i, s=40, color=INK2 if sig else "white", edgecolor=INK2, linewidth=1.5, zorder=3)
    ax.set_xscale("log"); ax.set_xticks([0.5, 0.75, 1, 1.5, 2]); ax.set_xticklabels(["0.5", "0.75", "1", "1.5", "2"])
    ax.minorticks_off(); ax.set_xlim(0.45, 2.3); ax.set_title(ttl); ax.grid(axis="y", visible=False)
axs[0].set_yticks(range(len(fo))); axs[0].set_yticklabels([AL[a] for a in fo])
fig.supxlabel("Odds ratio for a positive mention of the aspect, at the same star rating and property (log scale)",
              fontsize=9.3, color=INK2, y=-0.06)
save(fig, "fig11_behaviour_memory_or")

# ------------------------------------------------------------------ Fig 12 sentiment validity
fig, ax = plt.subplots(figsize=(5.2, 3.0))
data = [d.loc[d.Rating == s, "s_mean"].dropna() for s in [1, 2, 3, 4, 5]]
bp = ax.boxplot(data, widths=0.42, patch_artist=True, showfliers=False,
                medianprops=dict(color=INK, lw=1.5), whiskerprops=dict(color=MUTED, lw=1),
                capprops=dict(color=MUTED, lw=1), boxprops=dict(lw=0))
for patch, s in zip(bp["boxes"], [1, 2, 3, 4, 5]):
    patch.set_facecolor(STAR[s])
ax.set_xticks(range(1, 6)); ax.set_xticklabels([f"{s}★\nn={len(x):,}" for s, x in zip([1, 2, 3, 4, 5], data)])
ax.axhline(0, color=AXIS, lw=0.8); ax.set_ylabel("Mean sentence sentiment (VADER)"); ax.grid(axis="x", visible=False)
save(fig, "fig12_sentiment_by_rating")
print("figures written to", OUTD)
