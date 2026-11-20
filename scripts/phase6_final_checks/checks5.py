"""Phase 6, part 5: stand-alone values quoted in Chapter 4 and Appendix B.
1 robustness of the Ryokan and Hotel rating difference (Table 16)   2 review-level effect size
3 crowding language and ratings within properties; crowding in peak and other months (Section 4.4.3)
Usage (from the package folder, after phase5 location.py has written crowdflags.pkl):
    python phase6_final_checks/checks5.py data/phase3_review_features.csv crowdflags.pkl"""
import sys, itertools, warnings, numpy as np, pandas as pd
import statsmodels.formula.api as smf, statsmodels.api as sm
from scipy import stats
warnings.filterwarnings("ignore")
d = pd.read_csv(sys.argv[1]); flags = pd.read_pickle(sys.argv[2])
d["log_words"] = np.log(d.n_words.clip(lower=1)); d["peak"] = d.Month.isin([3, 4, 10, 11]).astype(int)
d["era"] = pd.cut(d.Year, [2000, 2019, 2022, 2030], labels=["2005-2019", "2020-2022", "2023-2026"]).astype(str)
core = d[d.tier.isin(["Ryokan", "Hotel"])].copy()

def exact(vals_a, vals_b):
    """two-sided exact permutation test on |difference of group means| over all assignments"""
    allv = np.array(list(vals_a) + list(vals_b)); k = len(vals_a); obs = abs(np.mean(vals_a) - np.mean(vals_b)); n = hit = 0
    for idx in itertools.combinations(range(len(allv)), k):
        m = np.zeros(len(allv), bool); m[list(idx)] = True; n += 1
        hit += abs(allv[m].mean() - allv[~m].mean()) >= obs - 1e-12
    return hit, n

print("== 1. Rating difference: mean of Ryokan property means minus mean of Hotel property means")
pm = d.groupby(["prop", "tier"]).Rating.mean().reset_index()
r = pm[pm.tier == "Ryokan"].Rating.values; h = pm[pm.tier == "Hotel"].Rating.values; hit, n = exact(r, h)
print(f"main: {r.mean() - h.mean():+.3f}; exact p = {hit}/{n} = {hit / n:.3f}")
r6 = pm[(pm.tier == "Ryokan") | pm.prop.str.contains("Nazuna")].Rating.values; hit, n = exact(r6, h)
print(f"two Nazuna properties counted as Ryokans (six and three): {r6.mean() - h.mean():+.3f}; exact p = {hit}/{n} = {hit / n:.3f}")
for pr in pm[pm.tier.isin(["Ryokan", "Hotel"])].prop:
    q = pm[(pm.prop != pr) & pm.tier.isin(["Ryokan", "Hotel"])]
    print(f"   leaving out {pr:28s} {q[q.tier == 'Ryokan'].Rating.mean() - q[q.tier == 'Hotel'].Rating.mean():+.3f}")
m = smf.mixedlm("Rating ~ C(tier, Treatment('Hotel')) + C(era)", core, groups=core["prop"]).fit()
k = [i for i in m.params.index if "tier" in i][0]; print(f"mixed model with period control: {m.params[k]:+.3f} (standard error {m.bse[k]:.3f})")
for lab, sub in [("up to 2019", core[core.Year <= 2019]), ("2023 onward", core[core.Year >= 2023])]:
    print(f"review-level means, {lab}: Ryokan {sub[sub.tier == 'Ryokan'].Rating.mean():.2f}, Hotel {sub[sub.tier == 'Hotel'].Rating.mean():.2f}")

print("\n== 2. Review-level effect size")
a = core[core.tier == "Ryokan"].Rating; b = core[core.tier == "Hotel"].Rating; n1, n2 = len(a), len(b)
sp = np.sqrt(((n1 - 1) * a.var(ddof=1) + (n2 - 1) * b.var(ddof=1)) / (n1 + n2 - 2))
print(f"Ryokan {a.mean():.3f}, Hotel {b.mean():.3f}, gap {a.mean() - b.mean():.3f}; pooled SD {sp:.3f}; Cohen's d = {(a.mean() - b.mean()) / sp:.3f}")

print("\n== 3. Crowding language (reviews in the order of the raw files, as in phase5 location.py)")
import glob, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "phase5_location_crowding_anova"))
from common import U, TIER, NAME
raw = pd.concat([pd.read_csv(f) for f in sorted(glob.glob(U + "reviews_*.csv"))], ignore_index=True); raw["review_id"] = np.arange(len(raw))
raw["type"] = raw["Location Name"].map(TIER); raw["property"] = raw["Location Name"].map(NAME); raw["peak"] = raw.Month.isin([3, 4, 10, 11]).astype(int)
raw["log_words"] = np.log(raw.Text.astype(str).str.split().str.len().clip(lower=1))
e = raw.merge(flags, on="review_id", how="left"); assert e.exposed.notna().all()
ps = e.groupby(["type", "property"]).exposed.mean().mul(100)
print("share of reviews describing crowding, mean of property shares:", ps.groupby("type").mean().round(1).to_dict())
hit, n = exact(ps["Ryokan"].values, ps["Hotel"].values); print(f"   Ryokan and Hotel properties: exact p = {hit}/{n} = {hit / n:.3f}; ranges {ps['Ryokan'].min():.1f}-{ps['Ryokan'].max():.1f} and {ps['Hotel'].min():.1f}-{ps['Hotel'].max():.1f}")
for lab, sub in [("all ten properties", e), ("seven comparison properties", e[e.type != "Hybrid"])]:
    for f, name in [("Rating ~ exposed + C(property)", "property fixed effects"), ("Rating ~ exposed + log_words + C(property)", "property fixed effects and review length"),
                    ("Rating ~ exposed + refuge + log_words + C(property)", "property fixed effects, review length and refuge language")]:
        m = smf.ols(f, data=sub).fit(cov_type="HC3"); ci = m.conf_int().loc["exposed"]
        print(f"   {lab}, {name}: {m.params['exposed']:+.3f} (95% CI {ci[0]:+.3f}, {ci[1]:+.3f})")
hot = e[e.type == "Hotel"]; t = pd.crosstab(hot.peak, hot.exposed)
chi2, p_c, _, _ = stats.chi2_contingency(t.values, correction=False); odds = (t.loc[1, 1] / t.loc[1, 0]) / (t.loc[0, 1] / t.loc[0, 0])
print(f"Hotels: crowding in peak months {hot[hot.peak == 1].exposed.mean() * 100:.1f}% vs other months {hot[hot.peak == 0].exposed.mean() * 100:.1f}%; odds ratio {odds:.2f}; chi-square p = {p_c:.2f}")
m = smf.glm("exposed ~ peak", data=hot, family=sm.families.Binomial()).fit(); print(f"   logistic: odds ratio {np.exp(m.params['peak']):.2f}, p = {m.pvalues['peak']:.2f}")
m = smf.glm("exposed ~ peak + C(property)", data=hot, family=sm.families.Binomial()).fit(); print(f"   logistic with property: odds ratio {np.exp(m.params['peak']):.2f}, p = {m.pvalues['peak']:.2f}")
for lab, sub in [("2005-2019", hot[hot.Year <= 2019]), ("2023-2026", hot[hot.Year >= 2023])]:
    print(f"   Hotels, {lab}: {sub.exposed.mean() * 100:.1f}% of {len(sub)} reviews")
a_, b_ = hot[hot.Year <= 2019].exposed, hot[hot.Year >= 2023].exposed
t2 = np.array([[a_.sum(), len(a_) - a_.sum()], [b_.sum(), len(b_) - b_.sum()]]); print(f"   2023-2026 vs 2005-2019: chi-square p = {stats.chi2_contingency(t2, correction=False)[1]:.2f}")
