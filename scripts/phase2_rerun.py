"""
Phase 2 rerun. Usage: python phase2_rerun.py <processed_reviews_all.csv>
Needs: pandas numpy scipy statsmodels scikit-learn gensim nltk textblob tabulate
Sentiment here = TextBlob polarity (the method the July thesis actually used). BERT is a separate Colab step.
Everything printed is computed; nothing is hard-coded. Writes phase2_results.md.
"""
import sys, os, re, itertools, warnings
import numpy as np, pandas as pd
from scipy import stats
import statsmodels.formula.api as smf
from sklearn.feature_extraction.text import CountVectorizer, ENGLISH_STOP_WORDS
from sklearn.decomposition import LatentDirichletAllocation
from sklearn.metrics import normalized_mutual_info_score
from scipy.optimize import linear_sum_assignment
warnings.filterwarnings("ignore")
SEED = 42
out = []
def say(s=""):
    print(s); out.append(str(s))

# ------------------------------------------------------------------ load + classification
p = pd.read_csv(sys.argv[1] if len(sys.argv) > 1 else "processed_reviews_all.csv")
p["prop"] = p["Hotel_Name"]
TIER = {  # core ryokan / hotel / hybrid-boutique (Nazuna are a hotel-ryokan mix; Junei is a boutique hotel)
    "Kyokoyado Muromachi Yutone": "Ryokan", "Nishiyama Ryokan": "Ryokan", "Ryokufuso": "Ryokan", "Shiraume": "Ryokan",
    "Four Seasons Hotl Kyoto": "Hotel", "Hyatt Regency Kyoto": "Hotel", "Parkhyatt": "Hotel",
    "Nazuna Kyoto Gosho": "Hybrid", "Nazuna Kyoto Nijojo": "Hybrid", "Junei Hotel Kyoto": "Hybrid"}
p["tier"] = p["prop"].map(TIER)
p["era"] = pd.cut(p.Year, [2000, 2019, 2022, 2030], labels=["<=2019", "2020-22", "2023+"])
p["peak"] = p.Month.isin([3, 4, 10, 11]).astype(int)
p["peak_AprNov"] = p.Month.isin([4, 11]).astype(int)
p["non_en"] = p.Text.map(lambda s: sum(ord(c) > 127 for c in str(s)) / max(len(str(s)), 1)) > 0.3
p["five"] = (p.Rating == 5).astype(int)
p["tb"] = p["Sentiment"]  # verified identical to TextBlob(Cleaned_Text).polarity

say("## A. Classification used (three tiers)")
say(p.groupby(["tier", "prop"]).agg(n=("Rating", "size"), rating=("Rating", "mean"), share5=("five", "mean"),
    textblob=("tb", "mean"), first_year=("Year", "min")).round(3).to_markdown())

def perm(pm):
    vals, lab = pm.val.values, (pm.tier == "Ryokan").values; k = lab.sum()
    obs = vals[lab].mean() - vals[~lab].mean(); diffs = []
    for c in itertools.combinations(range(len(vals)), k):
        m = np.zeros(len(vals), bool); m[list(c)] = True; diffs.append(vals[m].mean() - vals[~m].mean())
    diffs = np.array(diffs); return obs, float((np.abs(diffs) >= abs(obs) - 1e-12).mean()), len(diffs)

def propgap(d, col):
    pm = d.groupby(["prop", "tier"])[col].mean().reset_index().rename(columns={col: "val"})
    return pm, perm(pm)

core = p[p.tier.isin(["Ryokan", "Hotel"])].copy()
core_en = core[~core.non_en]

# ------------------------------------------------------------------ B. ratings and sentiment, property level
say("\n## B. Ryokan (4) vs Hotel (3): ratings and TextBlob sentiment at the PROPERTY level")
for col in ["Rating", "five", "tb", "Return_Intent"]:
    pm, (obs, pv, n) = propgap(core, col)
    a, b = pm[pm.tier == "Ryokan"].val, pm[pm.tier == "Hotel"].val
    w = stats.ttest_ind(a, b, equal_var=False)
    say(f"- {col}: Ryokan {a.mean():.3f} vs Hotel {b.mean():.3f}; gap {obs:+.3f}; exact permutation p = {pv:.3f} ({n} assignments); Welch on property means t = {w.statistic:.2f}")
r, h = core.Rating[core.tier == "Ryokan"], core.Rating[core.tier == "Hotel"]
sp = np.sqrt((r.var() + h.var()) / 2)
say(f"- review-level (for comparison only; ignores clustering): d = {(r.mean()-h.mean())/sp:.3f}, n = {len(r)} vs {len(h)}")
hyb = p[p.tier == "Hybrid"].groupby("prop").Rating.mean().round(3).to_dict()
say(f"- hybrid properties (not in the comparison): {hyb}")
m = smf.mixedlm("Rating ~ C(tier, Treatment('Hotel')) + C(era)", core, groups=core["prop"]).fit(reml=True)
say(f"- mixed model, era-adjusted: Ryokan effect {m.params.iloc[1]:+.3f} stars (SE {m.bse.iloc[1]:.3f}); only 7 clusters, so the p-value is optimistic")
say("- leave-one-property-out (property-level gap in mean rating):")
for q in core.prop.unique():
    pm, _ = propgap(core[core.prop != q], "Rating")
    say(f"  - without {q}: {pm[pm.tier=='Ryokan'].val.mean() - pm[pm.tier=='Hotel'].val.mean():+.3f}")
pm, (obs, pv, n) = propgap(core_en, "Rating"); say(f"- excluding {int(core.non_en.sum())} likely non-English reviews: gap {obs:+.3f}, p = {pv:.3f}")
for lab_, mask in [("<=2019", core.Year <= 2019), ("2023+", core.Year >= 2023)]:
    x = core[mask]; pm, (obs, pv, n) = propgap(x, "Rating")
    say(f"- reviews {lab_} only (review-level means shown because some properties have very few reviews): Ryokan {x.Rating[x.tier=='Ryokan'].mean():.3f} vs Hotel {x.Rating[x.tier=='Hotel'].mean():.3f}")

# ------------------------------------------------------------------ C. rebuilt topic model
say("\n## C. Topic model rebuilt (lemmatised, names removed, k chosen by coherence)")
import nltk; nltk.download("wordnet", quiet=True)
from nltk.stem import WordNetLemmatizer
lem = WordNetLemmatizer()
from functools import lru_cache
@lru_cache(maxsize=None)
def lemma(w):
    return lem.lemmatize(lem.lemmatize(w, "v"), "n")
NAMES = set("shiraume hyatt regency park four seasons nazuna junei nishiyama ryokufuso yutone kyokoyado muromachi gosho nijojo "
            "kyoto japan japanese hotel ryokan inn gion nijo shijo karasuma imperial palace".split())
STOP = set(ENGLISH_STOP_WORDS) | NAMES | set("nt didn don ve ll just really also got get went".split())
def toks(t):
    ws = re.findall(r"[a-z]{3,}", str(t).lower())
    ws = [lemma(w) for w in ws]
    return [w for w in ws if w not in STOP and len(w) > 2]
p["tokens"] = p.Text.map(toks)
# drop property-specific vocabulary (staff names, signature features): >60% of a term's occurrences from one property
tmp = p[["prop", "tokens"]].explode("tokens").dropna()
dfc = tmp.groupby(["tokens", "prop"]).size().unstack(fill_value=0)
tot, conc = dfc.sum(axis=1), dfc.max(axis=1) / dfc.sum(axis=1)
drop = set(dfc.index[(tot >= 20) & (conc > 0.6)])
say(f"- property-specific terms removed: {len(drop)} (e.g. " + ", ".join(sorted(drop)[:30]) + ")")
p["tokens"] = p.tokens.map(lambda ws: [w for w in ws if w not in drop])
cv = CountVectorizer(analyzer=lambda x: x, min_df=10, max_df=0.5)
X = cv.fit_transform(p.tokens); vocab = np.array(cv.get_feature_names_out())
from gensim.corpora import Dictionary
from gensim.models import CoherenceModel
dic = Dictionary(p.tokens.tolist())
def topwords(model, n=10): return [list(vocab[np.argsort(c)[::-1][:n]]) for c in model.components_]
rows = []
for k in [4, 5, 6, 8]:
    lda = LatentDirichletAllocation(n_components=k, learning_method="batch", max_iter=30, random_state=SEED).fit(X)
    cm = CoherenceModel(topics=topwords(lda), texts=p.tokens.tolist(), dictionary=dic, coherence="c_v", processes=1).get_coherence()
    rows.append((k, round(cm, 3)))
say(pd.DataFrame(rows, columns=["k", "c_v coherence"]).to_markdown(index=False))
best = max(r[1] for r in rows)
K = min(r[0] for r in rows if r[1] >= best - 0.01)
say(f"- highest coherence {best}; smallest k within 0.01 of it: k = {K} (chosen for parsimony; check interpretability)")
lda = LatentDirichletAllocation(n_components=K, learning_method="batch", max_iter=50, random_state=SEED).fit(X)
theta = lda.transform(X); p["topic"] = theta.argmax(1)
for i, w in enumerate(topwords(lda, 12)): say(f"- topic {i}: " + ", ".join(w))
# stability across seeds (best Jaccard matching of top-10 words)
base = [set(w) for w in topwords(lda)]; jac = []
for s in [1, 2, 3, 4]:
    l2 = LatentDirichletAllocation(n_components=K, learning_method="batch", max_iter=50, random_state=s).fit(X)
    o = [set(w) for w in topwords(l2)]
    M = np.array([[len(a & b) / len(a | b) for b in o] for a in base]); ri, ci = linear_sum_assignment(-M); jac.append(M[ri, ci].mean())
say(f"- stability: mean best-match Jaccard of top-10 words across 4 reseeded runs = {np.mean(jac):.2f}")
say(f"- property leakage (normalised mutual information, dominant topic vs property): July topics = {normalized_mutual_info_score(p.prop, p.Topic):.3f}; rebuilt topics = {normalized_mutual_info_score(p.prop, p.topic):.3f}")
core = p.loc[core.index]  # re-attach topic columns
pt = pd.DataFrame(theta, index=p.index, columns=[f"t{i}" for i in range(K)])
core = core.join(pt)
say("- mean topic share by tier (rows = topics):")
say(pt.join(p.tier).groupby("tier").mean().T.round(3).to_markdown())

# ------------------------------------------------------------------ D. does topic content account for the rating gap?
say("\n## D. Aspect association: does the Ryokan effect shrink once topic content is controlled?")
tcols = [f"t{i}" for i in range(1, K)]
m0 = smf.mixedlm("Rating ~ C(tier, Treatment('Hotel')) + C(era)", core, groups=core["prop"]).fit(reml=True)
m1 = smf.mixedlm("Rating ~ C(tier, Treatment('Hotel')) + C(era) + " + " + ".join(tcols), core, groups=core["prop"]).fit(reml=True)
b0, b1 = m0.params.iloc[1], m1.params.iloc[1]
say(f"- Ryokan effect without topics: {b0:+.3f}; with topic shares: {b1:+.3f}; attenuation = {(b0-b1)/b0:.0%}")
say("- topic coefficients (reference = topic 0): " + ", ".join(f"t{i}: {m1.params[f't{i}']:+.2f}" for i in range(1, K)))

# ------------------------------------------------------------------ E. seasonality with equivalence margins
say("\n## E. Seasonality: type x peak interaction with equivalence margins (margin = 0.2 SD of the outcome)")
def h3(d, outcome, peakcol="peak", label=""):
    era_term = " + C(era)" if d.era.astype(str).nunique() > 1 else ""
    f = f"{outcome} ~ C(tier, Treatment('Hotel'))*{peakcol}{era_term}"
    mm = smf.mixedlm(f, d, groups=d["prop"]).fit(reml=True)
    k = [i for i in mm.params.index if peakcol in i and ":" in i][0]
    b, se = mm.params[k], mm.bse[k]; marg = 0.2 * d[outcome].std()
    lo, hi = b - 1.645 * se, b + 1.645 * se
    verdict = "equivalent (90% CI inside margin)" if (lo > -marg and hi < marg) else ("difference" if (lo > 0 or hi < 0) else "inconclusive")
    pk = mm.params[peakcol]; pse = mm.bse[peakcol]
    say(f"- {label}{outcome}: hotel peak effect {pk:+.3f} (95% CI {pk-1.96*pse:+.3f}, {pk+1.96*pse:+.3f}); interaction {b:+.3f} "
        f"(90% CI {lo:+.3f}, {hi:+.3f}) vs margin +/-{marg:.3f} -> {verdict}")
for o in ["Rating", "tb"]: h3(core, o)
h3(core, "Rating", "peak_AprNov", "peak = Apr+Nov, ")
h3(core[core.Year >= 2023], "Rating", "peak", "2023+ only, ")
h3(core[core.Year >= 2023], "tb", "peak", "2023+ only, ")
say(core.groupby(["tier", "peak"]).Rating.agg(["size", "mean"]).round(3).to_markdown())
say("- note: month = REVIEW posting month. A stay-date field is needed for a clean seasonality test.")

# ------------------------------------------------------------------ F. keyword proxy flags, rebuilt strictly
say("\n## F. Explicit-mention proxies (keyword based, to be validated on a hand-checked sample)")
tl = p.Text.str.lower()
p["mem_strict"] = tl.str.contains(r"memorable|unforgettable|never forget|will remember|always remember|once in a lifetime|memories|memory").astype(int)
p["ret_strict"] = tl.str.contains(r"(?:will|would|'ll|definitely|certainly|hope to|can't wait to|cannot wait to|want to|plan to|look forward to|wish to)\W+(?:\w+\W+){0,4}(?:return|come back|be back|stay again|visit again|go back|stay here again)|next time we|next time i").astype(int)
say(f"- July flags: Memorable {p.Memorable.mean():.1%}, Return_Intent {p.Return_Intent.mean():.1%} (the Memorable flag counts the word 'special'; Return_Intent counts any 'again')")
say(f"- strict flags: explicit memory words {p.mem_strict.mean():.1%}, explicit return intent {p.ret_strict.mean():.1%}")
c2 = p[p.tier.isin(["Ryokan", "Hotel"])]
for col in ["mem_strict", "ret_strict"]:
    pm = c2.groupby(["prop", "tier"])[col].mean().reset_index().rename(columns={col: "val"}); obs, pv, n = perm(pm)
    say(f"- {col}: Ryokan {pm[pm.tier=='Ryokan'].val.mean():.3f} vs Hotel {pm[pm.tier=='Hotel'].val.mean():.3f}; property-level gap {obs:+.3f}, permutation p = {pv:.3f}")
p.sample(60, random_state=SEED)[["Text", "mem_strict", "ret_strict"]].assign(human_mem="", human_ret="").to_csv("flag_validation_sample.csv", index=False)

open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "phase2_results.md"), "w").write("\n".join(out))
