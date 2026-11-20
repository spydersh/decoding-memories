import sys, itertools, warnings, numpy as np, pandas as pd
import statsmodels.formula.api as smf, statsmodels.api as sm
warnings.filterwarnings("ignore")
d = pd.read_csv("data/phase3_review_features.csv")
A = ["dining", "bath", "room", "staff_service", "location", "value_price", "culture"]
d["log_words"] = np.log(d.n_words.clip(lower=1)); core = d[d.tier.isin(["Ryokan", "Hotel"])].copy()
print("share of core reviews by property:"); print((core.prop.value_counts(normalize=True)).round(3).to_string())
f9 = " + ".join(f"pos_{a} + neg_{a}" for a in A) + " + C(Rating) + log_words + C(prop)"
for col in ["rec", "mem"]:
    print(col)
    for pr in core.prop.unique():
        m = smf.glm(f"{col} ~ {f9}", data=core[core.prop != pr], family=sm.families.Binomial()).fit(cov_type="HC0"); ci = m.conf_int()
        t = m.t_test("pos_staff_service - pos_room = 0")
        print(f"   without {pr:28s} staff OR {np.exp(m.params['pos_staff_service']):.2f} ({np.exp(ci.loc['pos_staff_service',0]):.2f}, {np.exp(ci.loc['pos_staff_service',1]):.2f}) p={m.pvalues['pos_staff_service']:.3f} | room OR {np.exp(m.params['pos_room']):.2f} p={m.pvalues['pos_room']:.3f} | contrast p={float(np.squeeze(t.pvalue)):.4f}")
    # per-type
    for t_ in ["Ryokan", "Hotel"]:
        m = smf.glm(f"{col} ~ {f9}", data=core[core.tier == t_], family=sm.families.Binomial()).fit(cov_type="HC0"); ci = m.conf_int()
        print(f"   {t_}: staff OR {np.exp(m.params['pos_staff_service']):.2f} ({np.exp(ci.loc['pos_staff_service',0]):.2f}, {np.exp(ci.loc['pos_staff_service',1]):.2f}) p={m.pvalues['pos_staff_service']:.3f}; room OR {np.exp(m.params['pos_room']):.2f} p={m.pvalues['pos_room']:.3f}")
# all ORs with CI for fig/table
for col in ["rec", "mem", "ret"]:
    m = smf.glm(f"{col} ~ {f9}", data=core, family=sm.families.Binomial()).fit(cov_type="HC0"); ci = m.conf_int()
    print(col, "; ".join(f"{a}: {np.exp(m.params['pos_'+a]):.2f} ({np.exp(ci.loc['pos_'+a,0]):.2f}-{np.exp(ci.loc['pos_'+a,1]):.2f}){'*' if m.pvalues['pos_'+a]<.05 else ''}" for a in A))
# culture reward by type: simple interaction spec
base = "Rating ~ " + " + ".join(f"pos_{a} + neg_{a}" for a in A) + " + log_words + C(prop)"
m = smf.ols(base + " + pos_culture:C(tier, Treatment('Hotel'))", data=core).fit(cov_type="HC3")
k = [i for i in m.params.index if "pos_culture:" in i][0]; ci = m.conf_int().loc[k]
print(f"culture x type (only this interaction): {m.params[k]:+.3f} ({ci[0]:+.3f}, {ci[1]:+.3f}) p={m.pvalues[k]:.4f}")
for a in ["dining", "staff_service", "room", "culture", "bath", "location"]:
    m = smf.ols(base + f" + pos_{a}:C(tier, Treatment('Hotel'))", data=core).fit(cov_type="HC3"); k = [i for i in m.params.index if f"pos_{a}:" in i][0]; ci = m.conf_int().loc[k]
    print(f"   reward x type for {a}: {m.params[k]:+.3f} ({ci[0]:+.3f}, {ci[1]:+.3f}) p={m.pvalues[k]:.4f}")
# reward vs |penalty| tests pooled & by type
for lab, sub in [("Pooled", core), ("Ryokan", core[core.tier == "Ryokan"]), ("Hotel", core[core.tier == "Hotel"])]:
    m = smf.ols(base, data=sub).fit(cov_type="HC3")
    print(lab, "; ".join(f"{a}: reward+penalty {m.params['pos_'+a]+m.params['neg_'+a]:+.2f} p={float(np.squeeze(m.t_test(f'pos_{a} + neg_{a} = 0').pvalue)):.3f}" for a in A), f"| adjR2 {m.rsquared_adj:.3f} n={len(sub)}")
# staff vs location
m = smf.ols(base, data=core).fit(cov_type="HC3"); t = m.t_test("pos_staff_service - pos_location = 0"); print("staff-location reward", float(np.squeeze(t.effect)), float(np.squeeze(t.pvalue)))
# crowding counts not here. low-box / rec counts per property
g = d.groupby(["prop", "tier"]).agg(n=("Rating", "size"), low=("Rating", lambda x: (x <= 3).sum()), rec=("rec", "sum"), mem=("mem", "sum"), ret=("ret", "sum"))
print(g.to_string())
print("overall shares: rec %.3f ret %.3f mem %.3f" % (d.rec.mean(), d.ret.mean(), d.mem.mean()))
print("property-level type means rec/ret/mem range:"); print((g[["rec","ret","mem"]].div(g.n, axis=0)).round(3).to_string())
