import glob, numpy as np, pandas as pd, warnings, itertools
warnings.filterwarnings("ignore")
from scipy import stats
import statsmodels.formula.api as smf, statsmodels.api as sm
from statsmodels.stats.multicomp import pairwise_tukeyhsd
from statsmodels.stats.oneway import anova_oneway
U=__import__("os").environ.get("DM_RAW","data_raw").rstrip("/")+"/"
TIER={"Kyokoyado_Muromachi_Yutone":"Ryokan","NISHIYAMA_RYOKAN":"Ryokan","Ryokufuso":"Ryokan","Shiraume":"Ryokan","Nazuna_Kyoto_Gosho":"Hybrid","Nazuna_Kyoto_Nijojo":"Hybrid","Four_Seasons_Hotel_Kyoto":"Hotel","Hyatt_Regency_Kyoto":"Hotel","Park_Hyatt_Kyoto":"Hotel","The_Junei_Hotel":"Hybrid"}
df=pd.concat([pd.read_csv(f) for f in sorted(glob.glob(U+"reviews_*.csv"))],ignore_index=True)
df["tier"]=df["Location Name"].map(TIER); df["prop"]=df["Location Name"]
print(df.columns.tolist())
core=df[df.tier!="Hybrid"].copy()
def eta(m): a=sm.stats.anova_lm(m,typ=2); return a, a.sum_sq.iloc[0]/a.sum_sq.sum()
# 1 one-way ANOVA (review level), 3 groups and 2 groups
for lab,d in [("3 types",df),("Ryokan vs Hotel",core)]:
    g=[x.Rating.values for _,x in d.groupby("tier")]
    F,p=stats.f_oneway(*g); w=anova_oneway(g,use_var="unequal"); H,pk=stats.kruskal(*g); lev=stats.levene(*g)
    a,e=eta(smf.ols("Rating ~ C(tier)",data=d).fit())
    print(f"\n[{lab}] one-way F({len(g)-1},{len(d)-len(g)})={F:.2f} p={p:.2g} eta2={e:.4f} | Welch F={w.statistic:.2f} df2={w.df_denom:.0f} p={w.pvalue:.2g} | Kruskal H={H:.2f} p={pk:.2g} | Levene W={lev.statistic:.1f} p={lev.pvalue:.2g}")
    print(d.groupby("tier").Rating.agg(["size","mean","std"]).round(3).to_string())
print(pairwise_tukeyhsd(df.Rating,df.tier))
# 2 one-way across 10 properties
g=[x.Rating.values for _,x in df.groupby("prop")]; F,p=stats.f_oneway(*g); a,e=eta(smf.ols("Rating ~ C(prop)",data=df).fit())
print(f"\n[10 properties] F(9,{len(df)-10})={F:.2f} p={p:.2g} eta2={e:.4f}")
# 3 nested ANOVA: type tested against property-within-type (core 7 props)
m=smf.ols("Rating ~ C(tier) + C(prop)",data=core).fit()
gm=core.Rating.mean(); pm=core.groupby(["tier","prop"]).Rating.agg(["size","mean"]).reset_index(); tm=core.groupby("tier").Rating.agg(["size","mean"])
ss_type=sum(tm["size"]*(tm["mean"]-gm)**2); 
ss_prop=sum(r["size"]*(r["mean"]-tm.loc[r.tier,"mean"])**2 for _,r in pm.iterrows())
ss_err=sum(((x.Rating-x.Rating.mean())**2).sum() for _,x in core.groupby("prop")); ss_tot=((core.Rating-gm)**2).sum()
df_t,df_p,df_e=1,len(pm)-2,len(core)-len(pm)
F_nested=(ss_type/df_t)/(ss_prop/df_p); p_nested=1-stats.f.cdf(F_nested,df_t,df_p)
F_prop=(ss_prop/df_p)/(ss_err/df_e); p_prop=1-stats.f.cdf(F_prop,df_p,df_e)
print(f"\n[nested, core] SS type={ss_type:.1f} ({ss_type/ss_tot:.1%}), property within type={ss_prop:.1f} ({ss_prop/ss_tot:.1%}), residual={ss_err:.1f} ({ss_err/ss_tot:.1%})")
print(f"  type tested against property(type): F(1,{df_p})={F_nested:.2f} p={p_nested:.3f} | property within type: F({df_p},{df_e})={F_prop:.2f} p={p_prop:.2g}")
print(f"  naive type F against residual: {(ss_type/df_t)/(ss_err/df_e):.1f}")
# ICC
icc=(ss_prop/df_p - ss_err/df_e)
n0=(len(core)-sum(pm['size']**2)/len(core))/(len(pm)-1)
print("  n0=%.0f"%n0)
# 4 two-way type x peak
core["peak"]=core.Month.isin([3,4,10,11]).astype(int) if "Month" in core else 0
print("\npeak share:",core.peak.mean().round(3))
m2=smf.ols("Rating ~ C(tier)*C(peak)",data=core).fit(); print(sm.stats.anova_lm(m2,typ=2).round(4).to_string())
print(core.groupby(["tier","peak"]).Rating.agg(["size","mean"]).round(3).to_string())
