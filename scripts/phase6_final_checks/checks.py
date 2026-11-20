"""Phase 6: checks requested by the external evaluation.
1 exact permutation tests (one procedure, every table)   2 H3 with 95% intervals in every specification
3 H1: precision, leave-one-property-out, per-property contrasts   4 aspect attribution: single-aspect sentences
Usage: python checks.py <phase3_review_features.csv> <phase3_sentences.pkl>"""
import sys, re, itertools, warnings, numpy as np, pandas as pd
import statsmodels.formula.api as smf
from scipy import stats
warnings.filterwarnings("ignore")
d = pd.read_csv(sys.argv[1]); sent = pd.read_pickle(sys.argv[2])
A = ["dining", "bath", "room", "staff_service", "location", "value_price", "culture"]
d["log_words"] = np.log(d.n_words.clip(lower=1)); d["low"] = (d.Rating <= 3).astype(int); d["top"] = (d.Rating == 5).astype(int)
d["era"] = pd.cut(d.Year, [2000, 2019, 2022, 2030], labels=["a", "b", "c"]).astype(str)
d["peak"] = d.Month.isin([3, 4, 10, 11]).astype(int); d["peak2"] = d.Month.isin([4, 11]).astype(int)
core = d[d.tier.isin(["Ryokan", "Hotel"])].copy()

def exact(df, col):
    pm = df.groupby(["prop", "tier"])[col].mean().reset_index(); v = pm[col].values; r = (pm.tier == "Ryokan").values
    obs = v[r].mean() - v[~r].mean()
    ds = np.array([v[list(c)].mean() - np.delete(v, list(c)).mean() for c in itertools.combinations(range(len(v)), int(r.sum()))])
    two = (np.abs(ds) >= abs(obs) - 1e-12).mean(); one = ((ds >= obs - 1e-12).mean() if obs > 0 else (ds <= obs + 1e-12).mean())
    sep = "complete" if (v[r].min() > v[~r].max() or v[r].max() < v[~r].min()) else "overlap"
    return v[r].mean(), v[~r].mean(), obs, two, one, sep, int((np.abs(ds) >= abs(obs) - 1e-12).sum())

print("== 1. Exact permutation tests (two-sided on |difference in property means|; 35 assignments)")
for col in ["Rating", "top", "low", "s_mean", "textblob", "rec", "ret", "mem"]:
    R, H, o, two, one, sep, k = exact(core, col)
    print(f"{col:9s} R {R:.4f} H {H:.4f} diff {o:+.4f} | two-sided p = {k}/35 = {two:.3f} | one-sided {one:.3f} | {sep}")
for a in A:
    sub = core[core["mention_" + a] == 1]
    out = [exact(core, "mention_" + a), exact(sub, "sent_" + a), exact(sub, "neg_" + a)]
    print(f"{a:14s} " + " | ".join(f"{n}: R {x[0]:.3f} H {x[1]:.3f} p={x[3]:.3f} {x[5]}" for n, x in zip(["salience", "sentiment", "negshare"], out)))

print("\n== 2. H3 mixed models: 95% intervals for every specification")
def h3(df, y, pk, lab):
    era = " + C(era)" if df.era.nunique() > 1 else ""
    res = {}
    for ref in ["Hotel", "Ryokan"]:
        m = smf.mixedlm(f"{y} ~ C(tier, Treatment('{ref}'))*{pk}{era}", df, groups=df["prop"]).fit(reml=True)
        ci = m.conf_int(); res[ref] = (m.params[pk], ci.loc[pk, 0], ci.loc[pk, 1], m.pvalues[pk])
        if ref == "Hotel":
            k = [i for i in m.params.index if ":" in i][0]; res["int"] = (m.params[k], ci.loc[k, 0], ci.loc[k, 1], m.pvalues[k])
    f = lambda t: f"{t[0]:+.3f} ({t[1]:+.3f}, {t[2]:+.3f}) p={t[3]:.3f}"
    print(f"{lab} [n={len(df)}]\n   hotel peak {f(res['Hotel'])}\n   ryokan peak {f(res['Ryokan'])}\n   interaction {f(res['int'])}")
h3(core, "Rating", "peak", "Main, all years, peak = Mar Apr Oct Nov")
h3(core, "Rating", "peak2", "Peak = Apr and Nov")
h3(core[core.Year >= 2023], "Rating", "peak", "2023 onward")
h3(core[core.Year <= 2019], "Rating", "peak", "Up to 2019")
h3(core, "s_mean", "peak", "Outcome: review sentiment (VADER)")
print(core.groupby(["tier", "peak"]).Rating.agg(["size", "mean"]).round(3).to_string())

print("Property-level peak-season change (peak mean minus off-peak mean) and exact test:")
pp = core.groupby(["prop", "tier", "peak"]).Rating.mean().unstack("peak"); pp["chg"] = pp[1] - pp[0]
nn = core.groupby(["prop", "peak"]).size().unstack("peak"); print(pp.round(3).join(nn, rsuffix="_n").to_string())
tmp = pp.reset_index(); v = tmp.chg.values; r = (tmp.tier == "Ryokan").values; obs = v[r].mean() - v[~r].mean()
ds = np.array([v[list(c)].mean() - np.delete(v, list(c)).mean() for c in itertools.combinations(range(7), 4)])
print(f"   ryokan mean change {v[r].mean():+.3f}, hotel mean change {v[~r].mean():+.3f}, diff {obs:+.3f}; two-sided exact p = {(np.abs(ds)>=abs(obs)-1e-12).sum()}/35; one-sided {(ds>=obs-1e-12).sum()}/35")
for lab, sub in [("Apr+Nov", core.assign(peak=core.peak2)), ("2023+", core[core.Year >= 2023])]:
    q = sub.groupby(["prop", "tier", "peak"]).Rating.mean().unstack("peak"); q["chg"] = q[1] - q[0]; t = q.reset_index(); v = t.chg.values; r = (t.tier == "Ryokan").values; obs = v[r].mean() - v[~r].mean()
    ds = np.array([v[list(c)].mean() - np.delete(v, list(c)).mean() for c in itertools.combinations(range(7), 4)])
    print(f"   [{lab}] changes: " + ", ".join(f"{p_[:12]} {c:+.3f}" for p_, c in zip(t.prop, t.chg)) + f" | diff {obs:+.3f}; two-sided exact p = {(np.abs(ds)>=abs(obs)-1e-12).sum()}/35")
print("\n== 3. H1: staff-and-service versus room")
f6 = "Rating ~ " + " + ".join(f"pos_{a} + neg_{a}" for a in A) + " + log_words + C(prop)"
def contrasts(df, f=f6):
    m = smf.ols(f, data=df).fit(cov_type="HC3")
    t1 = m.t_test("pos_staff_service - pos_room = 0"); t2 = m.t_test("neg_staff_service - neg_room = 0")
    sq = lambda x: float(np.squeeze(x)); c1, c2 = np.squeeze(t1.conf_int()), np.squeeze(t2.conf_int())
    return m, (sq(t1.effect), c1[0], c1[1], sq(t1.pvalue)), (sq(t2.effect), c2[0], c2[1], sq(t2.pvalue))
for lab, sub in [("Pooled", core), ("Ryokan", core[core.tier == "Ryokan"]), ("Hotel", core[core.tier == "Hotel"])]:
    m, r, p = contrasts(sub); ci = m.conf_int()
    print(f"{lab}: reward staff-room {r[0]:+.3f} (95% CI {r[1]:+.3f}, {r[2]:+.3f}) p={r[3]:.2g} | penalty staff-room {p[0]:+.3f} (95% CI {p[1]:+.3f}, {p[2]:+.3f}) p={p[3]:.2f}")
    for a in A:
        print(f"    {a:14s} reward {m.params['pos_'+a]:+.3f} ({ci.loc['pos_'+a,0]:+.3f}, {ci.loc['pos_'+a,1]:+.3f}) p={m.pvalues['pos_'+a]:.3f} | penalty {m.params['neg_'+a]:+.3f} ({ci.loc['neg_'+a,0]:+.3f}, {ci.loc['neg_'+a,1]:+.3f}) p={m.pvalues['neg_'+a]:.3f} | n_pos {int(sub['pos_'+a].sum())} n_neg {int(sub['neg_'+a].sum())}")
print("Leave one property out (pooled model):")
for pr in core.prop.unique():
    m, r, p = contrasts(core[core.prop != pr])
    print(f"   without {pr:28s} reward diff {r[0]:+.3f} (p={r[3]:.2g}) | penalty diff {p[0]:+.3f} (p={p[3]:.2f})")
print("Within each property separately (no fixed effects needed):")
fp = "Rating ~ " + " + ".join(f"pos_{a} + neg_{a}" for a in A) + " + log_words"
est = []
for pr, sub in core.groupby("prop"):
    try:
        m = smf.ols(fp, data=sub).fit(cov_type="HC3"); t = m.t_test("pos_staff_service - pos_room = 0")
        est.append((pr, sub.tier.iloc[0], len(sub), float(np.squeeze(t.effect)), float(np.squeeze(t.pvalue)), m.params["pos_staff_service"], m.params["pos_room"]))
        print(f"   {pr:28s} n={len(sub):5d} staff reward {m.params['pos_staff_service']:+.3f} room reward {m.params['pos_room']:+.3f} diff {float(np.squeeze(t.effect)):+.3f} p={float(np.squeeze(t.pvalue)):.3f}")
    except Exception as e: print("   ", pr, "failed", e)
k = sum(e[3] > 0 for e in est); n = len(est)
print(f"   positive in {k} of {n} properties; two-sided sign test p = {stats.binomtest(k, n, 0.5).pvalue:.3f}; mean of property contrasts {np.mean([e[3] for e in est]):+.3f}, t-test p = {stats.ttest_1samp([e[3] for e in est], 0).pvalue:.3f}")
# property-level cluster bootstrap is not attempted (7 clusters)
# logistic contrasts
import statsmodels.api as sm
f9 = " + ".join(f"pos_{a} + neg_{a}" for a in A) + " + C(Rating) + log_words + C(prop)"
for col in ["rec", "mem", "ret"]:
    m = smf.glm(f"{col} ~ {f9}", data=core, family=sm.families.Binomial()).fit(cov_type="HC0"); t = m.t_test("pos_staff_service - pos_room = 0"); ci = m.conf_int()
    print(f"{col}: staff OR {np.exp(m.params['pos_staff_service']):.2f} ({np.exp(ci.loc['pos_staff_service',0]):.2f}, {np.exp(ci.loc['pos_staff_service',1]):.2f}) | room OR {np.exp(m.params['pos_room']):.2f} ({np.exp(ci.loc['pos_room',0]):.2f}, {np.exp(ci.loc['pos_room',1]):.2f}) | contrast p={float(np.squeeze(t.pvalue)):.2g}")
    lo = []
    for pr in core.prop.unique():
        mm = smf.glm(f"{col} ~ {f9}", data=core[core.prop != pr], family=sm.families.Binomial()).fit(cov_type="HC0")
        lo.append((np.exp(mm.params["pos_staff_service"]), mm.pvalues["pos_staff_service"]))
    print("     leave-one-out staff OR range %.2f to %.2f; max p %.3f" % (min(x[0] for x in lo), max(x[0] for x in lo), max(x[1] for x in lo)))

print("\n== 4. Aspect attribution: sentences that mention one aspect only")
RX = {"dining": r"kaiseki|breakfast|dinner|lunch|\bmeals?\b|\bfood\b|\bcourses?\b|matcha|tofu|restaurant|menu|\bchef|\bsake\b|cuisine",
      "bath": r"onsen|\bbath(?!room)|bathing|hot spring|\bsoak|yukata|sauna|\bspa\b|\bpool\b|ofuro|rotenburo|hinoki",
      "room": r"\brooms?\b|\bbeds?\b|futon|tatami|pillow|shower|toilet|bathroom|noise|noisy|\bview|spacious|decor|\bclean",
      "staff_service": r"\bstaff|service|hospitalit|welcom|attentive|helpful|friendly|concierge|\bowner|okami|\bhost|omotenashi|check.?in|check.?out|reception|\bmanager",
      "location": r"location|located|\bwalk|station|\bbus\b|taxi|subway|\btrain|distance|temple|\bgion\b|shrine|\bstreet|alley|neighbo",
      "value_price": r"\bprice|\bvalue\b|\bcost|expensive|\bworth|\bmoney\b|\brate\b|\bfees?\b|pricey|overpriced|cheap|afford",
      "culture": r"tradition|authentic|cultur|garden|atmospher|ambien|historic|machiya|kimono|ceremony|japanese style|heritage"}
low = sent.sentence.str.lower()
for a in A: sent["asp_" + a] = low.str.contains(RX[a], regex=True)
sent["n_asp"] = sent[["asp_" + a for a in A]].sum(1)
any_ = sent[sent.n_asp >= 1]
print(f"sentences: {len(sent)}; with at least one aspect: {len(any_)} ({len(any_)/len(sent):.1%}); of these, one aspect only: {(any_.n_asp==1).mean():.1%}; two or more: {(any_.n_asp>=2).mean():.1%}")
for a in A:
    sa = sent[sent["asp_" + a]]; print(f"   {a:14s} sentences {len(sa):6d}; single-aspect share {(sa.n_asp==1).mean():.1%}")
single = sent[sent.n_asp == 1]
e = d[["rid", "prop", "tier", "Rating", "log_words"]].copy()
for a in A:
    sm_ = single[single["asp_" + a]].groupby("rid").vader.mean(); e["sent_" + a] = e.rid.map(sm_)
    e["pos_" + a] = (e["sent_" + a] >= 0.05).astype(int); e["neg_" + a] = (e["sent_" + a] <= -0.05).astype(int)
ec = e[e.tier.isin(["Ryokan", "Hotel"])]
for lab, sub, sub0 in [("Pooled", ec, core), ("Ryokan", ec[ec.tier == "Ryokan"], core[core.tier == "Ryokan"]), ("Hotel", ec[ec.tier == "Hotel"], core[core.tier == "Hotel"])]:
    m, r, p = contrasts(sub); m0, r0, p0 = contrasts(sub0)
    print(f"{lab}: single-aspect: reward staff-room {r[0]:+.3f} (95% CI {r[1]:+.3f}, {r[2]:+.3f}) p={r[3]:.2g}; penalty diff {p[0]:+.3f} p={p[3]:.2f}; adjR2 {m.rsquared_adj:.3f} | all sentences: {r0[0]:+.3f}, adjR2 {m0.rsquared_adj:.3f}")
    for a in A:
        print(f"    {a:14s} reward {m.params['pos_'+a]:+.3f}{'*' if m.pvalues['pos_'+a]<.05 else ' '} penalty {m.params['neg_'+a]:+.3f}{'*' if m.pvalues['neg_'+a]<.05 else ' '} (n_neg {int(sub['neg_'+a].sum())}) | all: reward {m0.params['pos_'+a]:+.3f}{'*' if m0.pvalues['pos_'+a]<.05 else ' '} penalty {m0.params['neg_'+a]:+.3f}{'*' if m0.pvalues['neg_'+a]<.05 else ' '}")
# culture reward interaction with type under single-aspect coding
fi = "Rating ~ " + " + ".join(f"pos_{a} + neg_{a}" for a in A) + " + pos_culture:C(tier) + log_words + C(prop)"
for lab, df_ in [("all sentences", core), ("single-aspect", ec)]:
    m = smf.ols("Rating ~ " + " + ".join(f"(pos_{a} + neg_{a})*C(tier, Treatment('Hotel'))" for a in A) + " + log_words + C(prop)", data=df_).fit(cov_type="HC3")
    k = [i for i in m.params.index if "pos_culture:" in i or (":pos_culture" in i)][0]; ci = m.conf_int().loc[k]
    print(f"culture reward, ryokan minus hotel ({lab}): {m.params[k]:+.3f} (95% CI {ci[0]:+.3f}, {ci[1]:+.3f}) p={m.pvalues[k]:.3f}")
