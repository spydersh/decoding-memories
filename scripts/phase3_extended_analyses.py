"""
Phase 3: extended analyses with the data you already have (no new collection).
Usage:  python phase3_extended_analyses.py processed_reviews_all.csv [cache_dir]
Needs:  pandas numpy scipy statsmodels scikit-learn vaderSentiment tabulate
Writes: phase3_results.md and phase3_review_features.csv next to this script.

Sentiment = VADER at sentence level (lexicon proxy). Swap in validated BERT scores
(sentences_scored.csv from Colab) when available; every model below keeps the same form.
Comparison groups: 4 core ryokans vs 3 hotels; Nazuna x2 and Junei reported as "Hybrid".
NOTE: with 4 vs 3 properties there are only 35 possible group assignments, so the smallest possible
exact permutation p is 1/35 = .029 (complete separation). Report separation alongside p.
"""
import sys, os, re, itertools, warnings
import numpy as np, pandas as pd
from scipy import stats
import statsmodels.formula.api as smf
import statsmodels.api as sm
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer, ENGLISH_STOP_WORDS
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.model_selection import StratifiedKFold, LeaveOneGroupOut, cross_val_predict
from sklearn.metrics import roc_auc_score
warnings.filterwarnings("ignore")
SEED = 42
SRC = sys.argv[1] if len(sys.argv) > 1 else "processed_reviews_all.csv"
CACHE = sys.argv[2] if len(sys.argv) > 2 else "."
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "phase3_results.md")
lines = []
def say(s=""):
    print(s, flush=True); lines.append(str(s))
def save():
    open(OUT, "w").write("\n".join(lines))
def md(df, **k):
    return df.to_markdown(floatfmt=".3f", **k)

# ----------------------------------------------------------------------------- load
p = pd.read_csv(SRC)
p["prop"] = p["Hotel_Name"]
TIER = {"Kyokoyado Muromachi Yutone": "Ryokan", "Nishiyama Ryokan": "Ryokan", "Ryokufuso": "Ryokan",
        "Shiraume": "Ryokan", "Four Seasons Hotl Kyoto": "Hotel", "Hyatt Regency Kyoto": "Hotel",
        "Parkhyatt": "Hotel", "Nazuna Kyoto Gosho": "Hybrid", "Nazuna Kyoto Nijojo": "Hybrid",
        "Junei Hotel Kyoto": "Hybrid"}
p["tier"] = p["prop"].map(TIER)
p["rid"] = np.arange(len(p))
p["n_words"] = p.Text.astype(str).str.split().str.len()
p["log_words"] = np.log(p.n_words.clip(lower=1))
p["top"] = (p.Rating == 5).astype(int)
p["low"] = (p.Rating <= 3).astype(int)
p["textblob"] = p["Sentiment"]

# ----------------------------------------------------------------------------- sentences + VADER (cached)
cache_file = os.path.join(CACHE, "phase3_sentences.pkl")
if os.path.exists(cache_file):
    sent = pd.read_pickle(cache_file)
else:
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
    sia = SentimentIntensityAnalyzer()
    split = lambda t: [s.strip() for s in re.split(r"(?<=[.!?])\s+|\n+", str(t)) if len(s.strip()) > 2]
    sent = (p[["rid", "Text"]].assign(sentence=p.Text.map(split)).explode("sentence")
            .dropna(subset=["sentence"])[["rid", "sentence"]].reset_index(drop=True))
    sent["vader"] = sent.sentence.map(lambda s: sia.polarity_scores(s)["compound"])
    sent.to_pickle(cache_file)

ASPECTS = {  # pre-specified; identical dictionary must be used in the Colab BERT script
    "dining": r"kaiseki|breakfast|dinner|lunch|\bmeals?\b|\bfood\b|\bcourses?\b|matcha|tofu|restaurant|menu|\bchef|\bsake\b|cuisine",
    "bath": r"onsen|\bbath(?!room)|bathing|hot spring|\bsoak|yukata|sauna|\bspa\b|\bpool\b|ofuro|rotenburo|hinoki",
    "room": r"\brooms?\b|\bbeds?\b|futon|tatami|pillow|shower|toilet|bathroom|noise|noisy|\bview|spacious|decor|\bclean",
    "staff_service": r"\bstaff|service|hospitalit|welcom|attentive|helpful|friendly|concierge|\bowner|okami|\bhost|omotenashi|check.?in|check.?out|reception|\bmanager",
    "location": r"location|located|\bwalk|station|\bbus\b|taxi|subway|\btrain|distance|temple|\bgion\b|shrine|\bstreet|alley|neighbo",
    "value_price": r"\bprice|\bvalue\b|\bcost|expensive|\bworth|\bmoney\b|\brate\b|\bfees?\b|pricey|overpriced|cheap|afford",
    "culture": r"tradition|authentic|cultur|garden|atmospher|ambien|historic|machiya|kimono|ceremony|japanese style|heritage",
}
low = sent.sentence.str.lower()
for a, rx in ASPECTS.items():
    sent["asp_" + a] = low.str.contains(rx, regex=True)
sent["absv"] = sent.vader.abs()

g = sent.groupby("rid")
rv = pd.DataFrame({"n_sent": g.size(), "s_mean": g.vader.mean(), "s_min": g.vader.min(),
                   "s_max": g.vader.max(), "s_first": g.vader.first(), "s_last": g.vader.last()})
rv["s_peak"] = sent.loc[sent.groupby("rid")["absv"].idxmax(), ["rid", "vader"]].set_index("rid").vader
for a in ASPECTS:
    rv["sent_" + a] = sent[sent["asp_" + a]].groupby("rid").vader.mean()
d = p.join(rv, on="rid")
for a in ASPECTS:
    d["mention_" + a] = d["sent_" + a].notna().astype(int)
    d["pos_" + a] = (d["sent_" + a] >= 0.05).astype(int)
    d["neg_" + a] = (d["sent_" + a] <= -0.05).astype(int)

tl = d.Text.astype(str).str.lower()
d["mem"] = tl.str.contains(r"memorable|unforgettable|never forget|will remember|always remember|once in a lifetime|memories|memory").astype(int)
pos_ret = tl.str.contains(r"(?:will|would|'ll|definitely|certainly|hope to|can't wait to|cannot wait to|want to|plan to|look forward to|wish to)\W+(?:\w+\W+){0,4}(?:return|come back|be back|stay again|visit again|go back|stay here again)|next time we|next time i")
neg_ret = tl.str.contains(r"(?:\bnot|never|n't|\bno)\W+(?:\w+\W+){0,3}(?:return|come back|be back|stay again|go back)")
d["ret"] = (pos_ret & ~neg_ret).astype(int)
neg_rec = tl.str.contains(r"(?:\bnot|never|n't|cannot)\s+(?:\w+\s+){0,2}recommend")
d["rec"] = (tl.str.contains("recommend") & ~neg_rec).astype(int)
core = d[d.tier.isin(["Ryokan", "Hotel"])].copy()
A = list(ASPECTS)

def prop_compare(df, col):
    pm = df.groupby(["prop", "tier"])[col].mean().reset_index()
    R, H = pm[pm.tier == "Ryokan"][col], pm[pm.tier == "Hotel"][col]
    vals, lab = pm[col].values, (pm.tier == "Ryokan").values
    obs, diffs = R.mean() - H.mean(), []
    for c in itertools.combinations(range(len(vals)), lab.sum()):
        m = np.zeros(len(vals), bool); m[list(c)] = True; diffs.append(vals[m].mean() - vals[~m].mean())
    pv = float((np.abs(np.array(diffs)) >= abs(obs) - 1e-12).mean())
    sep = "complete" if (R.min() > H.max() or R.max() < H.min()) else "overlap"
    return R.mean(), H.mean(), obs, pv, sep

say("# Phase 3: extended analyses (computed; nothing hard-coded)")
say(f"Reviews: {len(d)}; sentences scored with VADER: {len(sent)}. Core comparison: 4 ryokans vs 3 hotels.")
say("With 4 vs 3 properties there are only 35 possible assignments, so the smallest exact p is 1/35 = .029; 'complete separation' (every ryokan beyond every hotel) is the strongest result possible.")

# ----------------------------------------------------------------------------- 1. KPIs
say("\n## 1. Business KPIs by property (top-box, low-box, net rating score)")
kp = d.groupby(["tier", "prop"]).agg(n=("Rating", "size"), mean=("Rating", "mean"), top_box=("top", "mean"),
                                     low_box=("low", "mean"), median_words=("n_words", "median"))
kp["net_score"] = kp.top_box - kp.low_box
say(md(kp))
for col in ["Rating", "top", "low"]:
    r, h, o, pv, sep = prop_compare(core, col)
    say(f"- {col}: Ryokan {r:.3f} vs Hotel {h:.3f} (property means), gap {o:+.3f}, exact p = {pv:.3f}, separation: {sep}")
save()

# ----------------------------------------------------------------------------- 2. length vs rating
say("\n## 2. Review length and rating (negativity elaboration)")
say(md(d.groupby("Rating").n_words.agg(["size", "median", "mean"]).rename(columns={"size": "n"})))
rho, pr = stats.spearmanr(d.Rating, d.n_words)
m = smf.ols("log_words ~ low + C(prop)", data=d).fit(cov_type="HC3")
say(f"- Spearman rating vs words: rho = {rho:.3f} (p = {pr:.2g})")
say(f"- within property, reviews rated <=3 are {np.exp(m.params['low'])-1:+.0%} longer (log-words model, property fixed effects)")
save()

# ----------------------------------------------------------------------------- 3. congruence
say("\n## 3. Rating-text congruence (how well lexicon sentiment tracks stars)")
for col in ["s_mean", "textblob", "s_min"]:
    rr, pp_ = stats.spearmanr(d.Rating, d[col], nan_policy="omit")
    auc = roc_auc_score(d.low[d[col].notna()], -d[col].dropna())
    say(f"- {col}: Spearman with rating = {rr:.3f}; AUC for detecting <=3-star reviews = {auc:.3f}")
mis5 = ((d.Rating == 5) & (d.s_mean < 0)).mean(); misl = ((d.Rating <= 2) & (d.s_mean > 0.3)).mean()
say(f"- incongruent cases: 5-star with negative mean sentiment {mis5:.1%}; 1-2 star with clearly positive mean sentiment {misl:.1%} of all reviews")
save()

# ----------------------------------------------------------------------------- 4. keyness
say("\n## 4. Distinctive vocabulary: property-balanced keyness (Ryokan vs Hotel)")
STOPK = set(ENGLISH_STOP_WORDS) | {"kyoto", "japan", "japanese", "hotel", "hotels", "ryokan", "ryokans", "inn", "stay", "stayed", "staying"}
cvk = CountVectorizer(token_pattern=r"(?u)\b[a-z][a-z]+\b", ngram_range=(1, 2), min_df=25, stop_words=list(STOPK))
Xb = (cvk.fit_transform(core.Text.astype(str)) > 0).astype(int)
voc = np.array(cvk.get_feature_names_out())
props = core.prop.values
rates = pd.DataFrame({pr_: np.asarray(Xb[props == pr_].mean(0)).ravel() for pr_ in np.unique(props)}, index=voc)
conc = rates.max(1) / rates.sum(1)
rates = rates[conc <= 0.5]  # drop property-specific terms (names, signature features)
rc = [c for c in rates.columns if TIER[c] == "Ryokan"]; hc = [c for c in rates.columns if TIER[c] == "Hotel"]
kt = pd.DataFrame({"ryokan_rate": rates[rc].mean(1), "hotel_rate": rates[hc].mean(1)})
kt["log_ratio"] = np.log((kt.ryokan_rate + 1e-3) / (kt.hotel_rate + 1e-3))
kt["separated"] = np.where(rates[rc].min(1) > rates[hc].max(1), "R>H all",
                           np.where(rates[rc].max(1) < rates[hc].min(1), "H>R all", ""))
say(f"- terms kept after removing property-specific vocabulary: {len(kt)} of {len(voc)}")
say("**Most ryokan-distinctive (share of reviews using the term, averaged across properties)**")
say(md(kt[kt.separated == "R>H all"].sort_values("log_ratio", ascending=False).head(20)))
say("**Most hotel-distinctive**")
say(md(kt[kt.separated == "H>R all"].sort_values("log_ratio").head(20)))
save()

# ----------------------------------------------------------------------------- 5. aspect salience and sentiment
say("\n## 5. Aspect salience (what guests narrate) and aspect sentiment, by type")
rows = []
for a in A:
    sR, sH, so, sp, ss = prop_compare(core, "mention_" + a)
    tmp = core[core["mention_" + a] == 1]
    eR, eH, eo, ep, es = prop_compare(tmp, "sent_" + a)
    nR, nH, no, np_, ns = prop_compare(tmp, "neg_" + a)
    hy = d[d.tier == "Hybrid"]
    rows.append([a, sR, sH, ss, eR, eH, es, nR, nH, ns, hy["mention_" + a].mean()])
asp = pd.DataFrame(rows, columns=["aspect", "salience_R", "salience_H", "sal_sep", "sentiment_R", "sentiment_H",
                                  "sent_sep", "neg_share_R", "neg_share_H", "neg_sep", "salience_hybrid"]).set_index("aspect")
say(md(asp))
say("- salience = share of reviews mentioning the aspect; sentiment = mean VADER of those sentences; neg_share = share of mentions that are negative. All averaged across properties.")
save()

# ----------------------------------------------------------------------------- 6. three-factor / penalty-reward
say("\n## 6. Asymmetric impact (three-factor theory, penalty-reward contrast)")
say("Rating ~ positive and negative mentions of each aspect + log length + property fixed effects (OLS, HC3).")
say("Reward = effect of a positive mention; penalty = effect of a negative mention. Test: reward - |penalty| = 0.")
f6 = "Rating ~ " + " + ".join([f"pos_{a} + neg_{a}" for a in A]) + " + log_words + C(prop)"
imp = {}
for lab, sub in [("Ryokan", core[core.tier == "Ryokan"]), ("Hotel", core[core.tier == "Hotel"]), ("Pooled core", core)]:
    m = smf.ols(f6, data=sub).fit(cov_type="HC3")
    out = []
    for a in A:
        rw, pn = m.params["pos_" + a], m.params["neg_" + a]
        tt = m.t_test(f"pos_{a} + neg_{a} = 0"); pdiff = float(tt.pvalue)
        cls = ("excitement (reward > penalty)" if (pdiff < .05 and rw + pn > 0) else
               "basic (penalty > reward)" if (pdiff < .05 and rw + pn < 0) else "performance (symmetric)")
        nneg = int(sub["neg_" + a].sum())
        out.append([a, rw, m.pvalues["pos_" + a], pn, m.pvalues["neg_" + a], int(sub["pos_" + a].sum()), nneg,
                    cls + (" [few negatives]" if nneg < 30 else "")])
    t6 = pd.DataFrame(out, columns=["aspect", "reward", "p_reward", "penalty", "p_penalty", "n_pos", "n_neg", "factor"]).set_index("aspect")
    imp[lab] = t6
    say(f"\n**{lab}** (n = {len(sub)}, adj R2 = {m.rsquared_adj:.3f})")
    say(md(t6))
save()

# ----------------------------------------------------------------------------- 7. IPA
say("\n## 7. Importance-performance analysis (impact-range importance; Martilla & James quadrants)")
for lab in ["Ryokan", "Hotel"]:
    t = imp[lab].copy()
    sub = core[core.tier == lab]
    t["importance"] = t.reward.clip(lower=0) + (-t.penalty).clip(lower=0)
    t["performance"] = [sub.loc[sub["mention_" + a] == 1, "pos_" + a].mean() for a in t.index]  # share of mentions positive
    mi, mp = t.importance.mean(), t.performance.mean()
    t["quadrant"] = np.select([(t.importance >= mi) & (t.performance < mp), (t.importance >= mi) & (t.performance >= mp),
                               (t.importance < mi) & (t.performance < mp)],
                              ["Concentrate here", "Keep up the good work", "Low priority"], "Possible overkill")
    say(f"\n**{lab}**")
    say(md(t[["importance", "performance", "quadrant"]].sort_values("importance", ascending=False)))
save()

# ----------------------------------------------------------------------------- 8. peak-end
say("\n## 8. Peak-end test: do the most intense and the final sentences explain the rating beyond the average?")
pe = core[core.n_sent >= 3].copy()
pe["s_pe"] = (pe.s_peak + pe.s_last) / 2
z = lambda s: (s - s.mean()) / s.std()
for c in ["s_mean", "s_min", "s_max", "s_first", "s_last", "s_pe"]:
    pe["z_" + c] = z(pe[c])
specs = {"M1 mean only": "z_s_mean", "M2 peak-end only": "z_s_pe",
         "M3 mean + min + max + first + last": "z_s_mean + z_s_min + z_s_max + z_s_first + z_s_last"}
for k, rhs in specs.items():
    m = smf.ols(f"Rating ~ {rhs} + log_words + C(prop)", data=pe).fit(cov_type="HC3")
    say(f"- {k}: adj R2 = {m.rsquared_adj:.3f}")
    if k.startswith("M3"):
        ci = m.conf_int()
        for c in ["z_s_mean", "z_s_min", "z_s_max", "z_s_first", "z_s_last"]:
            say(f"  - {c[2:]}: {m.params[c]:+.3f} stars per SD (95% CI {ci.loc[c,0]:+.3f}, {ci.loc[c,1]:+.3f})")
say(f"- n = {len(pe)} reviews with >= 3 sentences. Note: 'last' = end of the written narrative, not of the stay.")
save()

# ----------------------------------------------------------------------------- 9. behaviour and memory proxies
say("\n## 9. Behavioural and memory proxies (explicit return intent, recommendation, memory words)")
say(md(core.groupby(["tier", "Rating"])[["ret", "rec", "mem"]].mean().unstack(0)))
for col in ["ret", "rec", "mem"]:
    r, h, o, pv, sep = prop_compare(core, col)
    say(f"- {col}: Ryokan {r:.3f} vs Hotel {h:.3f}, gap {o:+.3f}, exact p = {pv:.3f}, separation: {sep}")
say("\n**Which aspects are associated with each proxy beyond the star rating?** (logit, odds ratios; controls: rating, log length, property)")
f9 = " + ".join([f"pos_{a} + neg_{a}" for a in A]) + " + C(Rating) + log_words + C(prop)"
tabs = {}
for col in ["ret", "rec", "mem"]:
    m = smf.glm(f"{col} ~ {f9}", data=core, family=sm.families.Binomial()).fit(cov_type="HC0")
    tabs[col] = pd.Series({t: f"{np.exp(m.params[t]):.2f}{'*' if m.pvalues[t] < .05 else ''}"
                           for t in [f"{s}_{a}" for a in A for s in ("pos", "neg")]})
say(md(pd.DataFrame(tabs).rename(columns={"ret": "return_intent_OR", "rec": "recommend_OR", "mem": "memory_words_OR"})))
say("- * p < .05. OR > 1 = the aspect mention raises the odds of the proxy at the same star rating.")
save()

# ----------------------------------------------------------------------------- 10. early-warning classifier
say("\n## 10. Dissatisfaction early-warning model (text -> rating <= 3)")
STOPC = list(ENGLISH_STOP_WORDS | {"shiraume", "hyatt", "regency", "park", "seasons", "nazuna", "junei", "nishiyama",
                                    "ryokufuso", "yutone", "kyokoyado", "muromachi", "gosho", "nijojo", "tomoko"})
pipe = make_pipeline(TfidfVectorizer(ngram_range=(1, 2), min_df=5, stop_words=STOPC, sublinear_tf=True),
                     LogisticRegression(max_iter=3000, class_weight="balanced", C=2.0))
y, X = d.low.values, d.Text.astype(str).values
pr5 = cross_val_predict(pipe, X, y, cv=StratifiedKFold(5, shuffle=True, random_state=SEED), method="predict_proba")[:, 1]
say(f"- 5-fold cross-validated AUC (text model): {roc_auc_score(y, pr5):.3f}")
say(f"- baseline AUC (VADER mean sentiment only): {roc_auc_score(y, -d.s_mean.fillna(0)):.3f}")
prl = cross_val_predict(pipe, X, y, cv=LeaveOneGroupOut(), groups=d.prop.values, method="predict_proba")[:, 1]
say(f"- leave-one-property-out AUC (generalises to an unseen property): {roc_auc_score(y, prl):.3f}")
pipe.fit(X, y)
vec, lr = pipe.named_steps["tfidfvectorizer"], pipe.named_steps["logisticregression"]
vv, cf = np.array(vec.get_feature_names_out()), lr.coef_[0]
say("- strongest dissatisfaction signals: " + ", ".join(vv[np.argsort(cf)[::-1][:25]]))
save()

# ----------------------------------------------------------------------------- 11. trend
say("\n## 11. Long-run trend by type (rating ~ year x type + property fixed effects)")
m = smf.ols("Rating ~ Year:C(tier) + C(prop)", data=core).fit(cov_type="HC3")
for t in ["Hotel", "Ryokan"]:
    k = f"Year:C(tier)[{t}]"; ci = m.conf_int().loc[k]
    say(f"- {t}: {m.params[k]*10:+.3f} stars per decade (95% CI {ci[0]*10:+.3f}, {ci[1]*10:+.3f})")
save()

keep = ["rid", "prop", "tier", "Rating", "Year", "Month", "n_words", "n_sent", "s_mean", "s_min", "s_max", "s_first",
        "s_last", "s_peak", "textblob", "ret", "rec", "mem"] + [f"{s}_{a}" for a in A for s in ("mention", "sent", "pos", "neg")]
d[keep].to_csv(os.path.join(HERE, "phase3_review_features.csv"), index=False)
say("\nDone. Review-level features saved to phase3_review_features.csv.")
save()
