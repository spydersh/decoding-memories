from common import *
import statsmodels.formula.api as smf
from sklearn.feature_extraction.text import CountVectorizer, ENGLISH_STOP_WORDS
from sklearn.decomposition import LatentDirichletAllocation
df,s=load()
AL=list(A.values())
# ---------- reward-penalty + IPA with both measures
rows=[]
for col in ["vader","bert"]:
    d=feats(df,s,col); core=d[d.type!="Hybrid"].rename(columns={"property":"prop"})
    f="Rating ~ "+" + ".join([f"pos_{a} + neg_{a}" for a in A])+" + log_words + C(prop)"
    for lab,sub in [("Ryokan",core[core.type=="Ryokan"]),("Hotel",core[core.type=="Hotel"]),("Both types",core)]:
        m=smf.ols(f,data=sub).fit(cov_type="HC3")
        imp={a:max(m.params["pos_"+a],0)+max(-m.params["neg_"+a],0) for a in A}
        for a,al in A.items():
            perf=sub.loc[sub["mention_"+a]==1,"pos_"+a].mean()*100
            rows.append([col,lab,al,round(m.params["pos_"+a],3),round(m.pvalues["pos_"+a],4),round(m.params["neg_"+a],3),round(m.pvalues["neg_"+a],4),int(sub["pos_"+a].sum()),int(sub["neg_"+a].sum()),round(imp[a],3),round(perf,1),round(float(m.t_test(f"pos_{a} + neg_{a} = 0").pvalue),4)])
RP=pd.DataFrame(rows,columns=["measure","group","aspect","reward","p_reward","penalty","p_penalty","n_positive","n_negative","importance","performance","p_asymmetry"]); RP.to_csv("rewards.csv",index=False)
print(RP[(RP.measure=="vader")&(RP.group!="Both types")][["group","aspect","reward","penalty","importance","performance"]].to_string())
d=feats(df,s,"vader")
# ---------- correspondence analysis property x aspect (mention counts)
N=np.array([[d.loc[d.property==p,"mention_"+a].sum() for a in A] for p in NAME.values()],float)
P=N/N.sum(); r=P.sum(1); c=P.sum(0); S=np.diag(r**-.5)@(P-np.outer(r,c))@np.diag(c**-.5)
Uu,sv,Vt=np.linalg.svd(S,full_matrices=False); inert=sv**2/np.sum(sv**2)
F=np.diag(r**-.5)@Uu*sv; G=np.diag(c**-.5)@Vt.T*sv
ca=[["property",p,TIER[k],round(F[i,0],4),round(F[i,1],4)] for i,(k,p) in enumerate(NAME.items())]+[["aspect",al,"",round(G[j,0],4),round(G[j,1],4)] for j,al in enumerate(AL)]
CA=pd.DataFrame(ca,columns=["kind","label","type","dim1","dim2"]); CA["inertia1"]=round(inert[0]*100,1); CA["inertia2"]=round(inert[1]*100,1); CA.to_csv("perceptual.csv",index=False)
print(CA.to_string()); print("inertia",inert.round(3), "total inertia",np.sum(sv**2).round(4))
# ---------- trends by year
b=s.groupby("review_id").bert.mean().rename("bert_mean"); d=d.join(b,on="review_id")
rows=[]
for (t,y),g in d.groupby(["type","Year"]): rows.append(["type",t,t,int(y),len(g),round(g.Rating.mean(),3),round(g.low.mean()*100,1),round(g.s_mean.mean(),3),round(g.bert_mean.mean(),3)])
for (p,t,y),g in d.groupby(["property","type","Year"]): rows.append(["property",p,t,int(y),len(g),round(g.Rating.mean(),3),round(g.low.mean()*100,1),round(g.s_mean.mean(),3),round(g.bert_mean.mean(),3)])
TR=pd.DataFrame(rows,columns=["level","name","type","year","n","rating","low_share","vader","bert"]); TR.to_csv("trend.csv",index=False); print(TR[TR.level=="type"].pivot(index="year",columns="name",values="n").fillna(0).astype(int).T.to_string())
# ---------- seasonality
MN=["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
rows=[]
for (t,mth),g in d.groupby(["type","Month"]): rows.append([t,int(mth),MN[int(mth)-1],int(mth in (3,4,10,11)),len(g),round(g.Rating.mean(),3),round(g.low.mean()*100,1),round(g.bert_mean.mean(),3)])
SE=pd.DataFrame(rows,columns=["type","month","month_name","peak","n","rating","low_share","bert"]); SE.to_csv("season.csv",index=False); print(SE.pivot(index="type",columns="month",values="rating").round(2).to_string())
# ---------- aspect co-occurrence (lift) of positive / negative mentions, by type
rows=[]
for t in ["Ryokan","Hotel"]:
    g=d[d.type==t]
    for pol in ["pos","neg"]:
        for a,al in A.items():
            for b2,bl in A.items():
                if a==b2: rows.append([t,pol,al,bl,None,int(g[pol+"_"+a].sum()),None]); continue
                pa,pb=g[pol+"_"+a].mean(),g[pol+"_"+b2].mean(); pab=(g[pol+"_"+a]&g[pol+"_"+b2]).mean()
                rows.append([t,pol,al,bl,round(pab/(pa*pb),2) if pa*pb>0 else None,int((g[pol+"_"+a]&g[pol+"_"+b2]).sum()),round(pab/pa*100,1) if pa>0 else None])
CO=pd.DataFrame(rows,columns=["type","polarity","aspect_a","aspect_b","lift","n_both","share_of_a"]); CO.to_csv("cooccurrence.csv",index=False)
print(CO[(CO.polarity=="neg")&(CO.type=="Hotel")].pivot(index="aspect_a",columns="aspect_b",values="lift").to_string())
# ---------- distinctive vocabulary (property-balanced keyness, as in phase 3)
core=d[d.type!="Hybrid"]
STOPK=set(ENGLISH_STOP_WORDS)|{"kyoto","japan","japanese","hotel","hotels","ryokan","ryokans","inn","stay","stayed","staying"}
cvk=CountVectorizer(token_pattern=r"(?u)\b[a-z][a-z]+\b",ngram_range=(1,2),min_df=25,stop_words=list(STOPK))
Xb=(cvk.fit_transform(core.Text.astype(str))>0).astype(int); voc=np.array(cvk.get_feature_names_out()); props=core.property.values
rates=pd.DataFrame({p:np.asarray(Xb[props==p].mean(0)).ravel() for p in np.unique(props)},index=voc)
rates=rates[(rates.max(1)/rates.sum(1))<=0.5]
T2={v:TIER[k] for k,v in NAME.items()}; rc=[c for c in rates.columns if T2[c]=="Ryokan"]; hc=[c for c in rates.columns if T2[c]=="Hotel"]
kt=pd.DataFrame({"ryokan_rate":rates[rc].mean(1)*100,"hotel_rate":rates[hc].mean(1)*100}); kt["log_ratio"]=np.log((kt.ryokan_rate/100+1e-3)/(kt.hotel_rate/100+1e-3))
kt["sep"]=np.where(rates[rc].min(1)>rates[hc].max(1),"R",np.where(rates[rc].max(1)<rates[hc].min(1),"H",""))
W=pd.concat([kt[kt.sep=="R"].sort_values("log_ratio",ascending=False).head(20).assign(side="Ryokan"),kt[kt.sep=="H"].sort_values("log_ratio").head(20).assign(side="Hotel")]).reset_index().rename(columns={"index":"term"})
W["times"]=np.where(W.side=="Ryokan",(W.ryokan_rate+.1)/(W.hotel_rate+.1),(W.hotel_rate+.1)/(W.ryokan_rate+.1)).round(1)
for c in ["ryokan_rate","hotel_rate"]: W[c]=W[c].round(1)
W["log_ratio"]=W.log_ratio.round(3); W[["term","side","ryokan_rate","hotel_rate","log_ratio","times"]].to_csv("words.csv",index=False); print(W[["term","side","ryokan_rate","hotel_rate","times"]].to_string())
