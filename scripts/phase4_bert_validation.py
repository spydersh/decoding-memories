import glob, re, numpy as np, pandas as pd, warnings
warnings.filterwarnings("ignore")
from sklearn.metrics import cohen_kappa_score, f1_score, roc_auc_score, confusion_matrix, precision_recall_fscore_support
from sklearn.model_selection import StratifiedKFold
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
U=__import__("os").environ.get("DM_RAW","data_raw").rstrip("/")+"/"
TIER={"Kyokoyado_Muromachi_Yutone":"Ryokan","NISHIYAMA_RYOKAN":"Ryokan","Ryokufuso":"Ryokan","Shiraume":"Ryokan","Nazuna_Kyoto_Gosho":"Hybrid","Nazuna_Kyoto_Nijojo":"Hybrid","Four_Seasons_Hotel_Kyoto":"Hotel","Hyatt_Regency_Kyoto":"Hotel","Park_Hyatt_Kyoto":"Hotel","The_Junei_Hotel":"Hybrid"}
df=pd.concat([pd.read_csv(f) for f in sorted(glob.glob(U+"reviews_*.csv"))],ignore_index=True); df["review_id"]=np.arange(len(df)); df["tier"]=df["Location Name"].map(TIER)
s=pd.read_csv(U+"sentences_scored.csv")
lab=pd.read_csv("data/labeling_sample_human_labels.csv")
lab["row"]=np.arange(len(lab))
print("labels:",lab.human_label.value_counts().to_dict())
print("by colab type:\n",pd.crosstab(lab.type,lab.human_label))
m=lab.merge(s[["review_id","sentence","bert","textblob"]].drop_duplicates(["review_id","sentence"]),on=["review_id","sentence"],how="left").merge(df[["review_id","tier","Rating"]],on="review_id")
print("unmatched rows (sentence text lost):",m.bert.isna().sum(), m[m.bert.isna()].sentence.tolist())
m["nonascii"]=m.sentence.map(lambda x: sum(ord(c)>127 for c in x)/len(x)>.3)
m["nw"]=m.sentence.str.split().str.len()
ok=m[m.bert.notna()&~m.nonascii].copy()
sia=SentimentIntensityAnalyzer(); ok["vader"]=ok.sentence.map(lambda x:sia.polarity_scores(x)["compound"])
print("usable:",len(ok), ok.human_label.value_counts().to_dict(), "by tier:",pd.crosstab(ok.tier,ok.human_label).to_dict("index"))
cat=lambda x,t=.05: np.where(x>=t,"pos",np.where(x<=-t,"neg","neu"))
L=["neg","neu","pos"]; y=ok.human_label.values
print("\n== three-class, default threshold +-0.05")
for n in ["vader","bert","textblob"]:
    p=cat(ok[n].values); pr,rc,f,_=precision_recall_fscore_support(y,p,labels=L,zero_division=0)
    print(f"{n:9s} acc={np.mean(y==p):.3f} kappa={cohen_kappa_score(y,p):.3f} macroF1={f1_score(y,p,average='macro'):.3f} | neg P/R={pr[0]:.2f}/{rc[0]:.2f} neu P/R={pr[1]:.2f}/{rc[1]:.2f} pos P/R={pr[2]:.2f}/{rc[2]:.2f}")
    print(pd.DataFrame(confusion_matrix(y,p,labels=L),index=["H_"+l for l in L],columns=L).to_string())
print("always-pos baseline acc:",np.mean(y=="pos").round(3))
# calibrated bands by 5-fold CV (grid on symmetric/asymmetric cut-offs)
print("\n== calibrated neutral band (5-fold CV, max kappa)")
def cal(x,y,grid):
    skf=StratifiedKFold(5,shuffle=True,random_state=1); pred=np.empty(len(y),dtype=object); ch=[]
    for tr,te in skf.split(x,y):
        best=max(grid,key=lambda g:cohen_kappa_score(y[tr],np.where(x[tr]>=g[1],"pos",np.where(x[tr]<=g[0],"neg","neu"))))
        ch.append(best); pred[te]=np.where(x[te]>=best[1],"pos",np.where(x[te]<=best[0],"neg","neu"))
    return pred,ch
grids={"vader":[(a,b) for a in [-.5,-.4,-.3,-.2,-.1,-.05] for b in [.05,.1,.2,.3,.4]],
       "bert":[(a,b) for a in [-.999,-.998,-.995,-.99,-.98,-.95,-.9,-.5] for b in [-.5,0,.5,.9,.95,.98,.99,.995,.998]],
       "textblob":[(a,b) for a in [-.3,-.2,-.1,-.05,-.01] for b in [.01,.05,.1,.2,.3]]}
for n in grids:
    p,ch=cal(ok[n].values,y,grids[n]); pr,rc,f,_=precision_recall_fscore_support(y,p,labels=L,zero_division=0)
    print(f"{n:9s} CV kappa={cohen_kappa_score(y,p):.3f} acc={np.mean(y==p):.3f} macroF1={f1_score(y,p,average='macro'):.3f} neg P/R={pr[0]:.2f}/{rc[0]:.2f} neu P/R={pr[1]:.2f}/{rc[1]:.2f} cuts={ch}")
print("\n== threshold-free: AUC")
pn=ok[ok.human_label!="neu"]; 
for n in ["vader","bert","textblob"]:
    print(f"{n:9s} AUC pos-vs-neg (n={len(pn)}): {roc_auc_score(pn.human_label=='pos',pn[n]):.3f} | AUC neg-vs-rest: {roc_auc_score(ok.human_label=='neg',-ok[n]):.3f} | AUC pos-vs-rest: {roc_auc_score(ok.human_label=='pos',ok[n]):.3f}")
# bootstrap CI for kappa diff bert vs vader (default thresholds)
rng=np.random.RandomState(0); d=[]; kv=[]; kb=[]
pv,pb=cat(ok.vader.values),cat(ok.bert.values)
for _ in range(2000):
    i=rng.randint(0,len(ok),len(ok)); kv.append(cohen_kappa_score(y[i],pv[i])); kb.append(cohen_kappa_score(y[i],pb[i]))
kv,kb=np.array(kv),np.array(kb)
print("\nbootstrap kappa vader %.3f [%.3f,%.3f]; bert %.3f [%.3f,%.3f]; diff bert-vader [%.3f,%.3f]"%(np.mean(kv),*np.percentile(kv,[2.5,97.5]),np.mean(kb),*np.percentile(kb,[2.5,97.5]),*np.percentile(kb-kv,[2.5,97.5])))
print("\nvader-bert agreement on sign:",np.mean(np.sign(ok.vader)==np.sign(ok.bert)).round(3))
# label diagnostics
ok["vc"],ok["bc"],ok["tc"]=cat(ok.vader.values),cat(ok.bert.values),cat(ok.textblob.values)
allneg=ok[(ok.human_label=="pos")&(ok.vc!="pos")&(ok.bc=="neg")&(ok.tc!="pos")]
print("\nhuman=pos but no method positive (BERT neg):",len(allneg)); print(allneg[["row","sentence"]].to_string(max_colwidth=110))
fact=ok[(ok.human_label=="pos")&(ok.vc=="neu")&(ok.tc=="neu")]
print("\nhuman=pos, VADER & TextBlob neutral:",len(fact)); print(fact[["row","sentence","bert"]].head(40).to_string(max_colwidth=100))
print("\nhuman non-pos share by position: rows 0-149 (Colab Hotel) %.2f | rows 150-299 (Colab Ryokan) %.2f"%((lab.human_label[:150]!="pos").mean(),(lab.human_label[150:]!="pos").mean()))
for n in ["vc","bc"]: print(n,"non-pos share hotel rows %.2f, ryokan rows %.2f"%((ok[ok.row<150][n]!="pos").mean(),(ok[ok.row>=150][n]!="pos").mean()))
ok.to_csv("validation_300_scored.csv",index=False)


# ===== part 2: full-corpus robustness with BERT scores =====

import glob, re, itertools, numpy as np, pandas as pd, warnings
warnings.filterwarnings("ignore")
import statsmodels.formula.api as smf
from scipy import stats
from sklearn.metrics import roc_auc_score
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
U=__import__("os").environ.get("DM_RAW","data_raw").rstrip("/")+"/"
TIER={"Kyokoyado_Muromachi_Yutone":"Ryokan","NISHIYAMA_RYOKAN":"Ryokan","Ryokufuso":"Ryokan","Shiraume":"Ryokan","Nazuna_Kyoto_Gosho":"Hybrid","Nazuna_Kyoto_Nijojo":"Hybrid","Four_Seasons_Hotel_Kyoto":"Hotel","Hyatt_Regency_Kyoto":"Hotel","Park_Hyatt_Kyoto":"Hotel","The_Junei_Hotel":"Hybrid"}
df=pd.concat([pd.read_csv(f) for f in sorted(glob.glob(U+"reviews_*.csv"))],ignore_index=True); df["review_id"]=np.arange(len(df))
df["tier"]=df["Location Name"].map(TIER); df["prop"]=df["Location Name"]; df["log_words"]=np.log(df.Text.astype(str).str.split().str.len().clip(lower=1)); df["low"]=(df.Rating<=3).astype(int)
import os
s=pd.read_pickle("sent.pkl") if os.path.exists("sent.pkl") else pd.read_csv(U+"sentences_scored.csv").drop(columns=["Text"])
if "vader" not in s: s["vader"]=s.sentence.astype(str).map(lambda x:SentimentIntensityAnalyzer().polarity_scores(x)["compound"])
s.to_pickle("sent.pkl")
A=["dining","bath","room","staff_service","location","value_price","culture"]
print("sentence level: spearman vader-bert %.3f; sign agreement (vader!=0) %.3f; share bert<0: %.3f; share vader<=-.05: %.3f"%(stats.spearmanr(s.vader,s.bert)[0], (np.sign(s.vader[s.vader!=0])==np.sign(s.bert[s.vader!=0])).mean(), (s.bert<0).mean(), (s.vader<=-.05).mean()))
print("of VADER-neutral sentences, share BERT negative: %.3f"%((s.bert[(s.vader.abs()<.05)]<0).mean()))
def feats(col):
    g=s.groupby("review_id"); rv=pd.DataFrame({"s_mean":g[col].mean(),"s_min":g[col].min()})
    for a in A:
        x=s[s["asp_"+a]==1].groupby("review_id")[col].mean(); rv["sent_"+a]=x
    d=df.join(rv,on="review_id")
    for a in A:
        d["mention_"+a]=d["sent_"+a].notna().astype(int); d["pos_"+a]=(d["sent_"+a]>=.05).astype(int); d["neg_"+a]=(d["sent_"+a]<=-.05).astype(int)
    return d
def perm(core,col):
    pm=core.groupby(["prop","tier"])[col].mean().reset_index(); v=pm[col].values; lab=(pm.tier=="Ryokan").values; obs=v[lab].mean()-v[~lab].mean(); k=n=0
    for idx in itertools.combinations(range(len(v)),lab.sum()):
        mm=np.zeros(len(v),bool); mm[list(idx)]=True; n+=1; k+=abs(v[mm].mean()-v[~mm].mean())>=abs(obs)-1e-12
    sep="complete" if (v[lab].min()>v[~lab].max() or v[lab].max()<v[~lab].min()) else "overlap"
    return v[lab].mean(),v[~lab].mean(),obs,k/n,sep
res={}
for col in ["vader","bert"]:
    d=feats(col); core=d[d.tier.isin(["Ryokan","Hotel"])].copy(); res[col]=d
    print(f"\n================ {col.upper()}")
    print("review mean vs rating: spearman %.3f | AUC <=3 stars %.3f"%(stats.spearmanr(d.Rating,d.s_mean)[0], roc_auc_score(d.low,-d.s_mean)))
    print("mean sentiment by star:",d.groupby("Rating").s_mean.mean().round(3).to_dict())
    print("type comparison (property means): R %.3f H %.3f diff %+.3f exact p %.3f %s"%perm(core,"s_mean"))
    print(core.groupby(["tier","prop"]).s_mean.mean().round(3).to_dict())
    f="Rating ~ "+" + ".join([f"pos_{a} + neg_{a}" for a in A])+" + log_words + C(prop)"
    for lab,sub in [("Pooled",core),("Ryokan",core[core.tier=="Ryokan"]),("Hotel",core[core.tier=="Hotel"])]:
        m=smf.ols(f,data=sub).fit(cov_type="HC3")
        t=pd.DataFrame({"reward":[m.params["pos_"+a] for a in A],"p_r":[m.pvalues["pos_"+a] for a in A],"penalty":[m.params["neg_"+a] for a in A],"p_p":[m.pvalues["neg_"+a] for a in A],"n_pos":[int(sub["pos_"+a].sum()) for a in A],"n_neg":[int(sub["neg_"+a].sum()) for a in A],"p_asym":[float(m.t_test(f"pos_{a} + neg_{a} = 0").pvalue) for a in A]},index=A)
        print(f"-- {lab} n={len(sub)} adjR2={m.rsquared_adj:.3f}"); print(t.round(3).to_string())
        c1=m.t_test("pos_staff_service - pos_room = 0"); c2=m.t_test("neg_staff_service - neg_room = 0")
        print("   H1 contrasts: staff reward - room reward = %+.3f (p=%.4f); staff penalty - room penalty = %+.3f (p=%.3f)"%(float(np.ravel(c1.effect)[0]),float(np.ravel(c1.pvalue)[0]),float(np.ravel(c2.effect)[0]),float(np.ravel(c2.pvalue)[0])))
    # negative share of mentions for staff by tier property-level
    for a in ["staff_service","culture"]:
        core["ns"]=np.where(core["mention_"+a]==1,core["neg_"+a],np.nan)
        print(a,"negative share of mentions (property means): R %.3f H %.3f diff %+.3f p %.3f %s"%perm(core.dropna(subset=["ns"]),"ns"))
rv=res["vader"][["review_id","s_mean"]].merge(res["bert"][["review_id","s_mean"]],on="review_id",suffixes=("_v","_b"))
print("\nreview-level spearman vader-bert: %.3f"%stats.spearmanr(rv.s_mean_v,rv.s_mean_b)[0])
for a in A:
    v,b=res["vader"],res["bert"]; mm=v["mention_"+a]==1
    print(a,"neg-mention agreement: both %.0f vader-only %.0f bert-only %.0f"%(((v["neg_"+a]==1)&(b["neg_"+a]==1)).sum(),((v["neg_"+a]==1)&(b["neg_"+a]==0)).sum(),((v["neg_"+a]==0)&(b["neg_"+a]==1)).sum()))
