import glob, numpy as np, pandas as pd, warnings
warnings.filterwarnings("ignore")
from scipy import stats
U=__import__("os").environ.get("DM_RAW","data_raw").rstrip("/")+"/"
TIER={"Kyokoyado_Muromachi_Yutone":"Ryokan","NISHIYAMA_RYOKAN":"Ryokan","Ryokufuso":"Ryokan","Shiraume":"Ryokan","Nazuna_Kyoto_Gosho":"Hybrid","Nazuna_Kyoto_Nijojo":"Hybrid","Four_Seasons_Hotel_Kyoto":"Hotel","Hyatt_Regency_Kyoto":"Hotel","Park_Hyatt_Kyoto":"Hotel","The_Junei_Hotel":"Hybrid"}
NAME={"Kyokoyado_Muromachi_Yutone":"Muromachi Yutone","NISHIYAMA_RYOKAN":"Nishiyama Ryokan","Ryokufuso":"Ryokufuso","Shiraume":"Shiraume","Nazuna_Kyoto_Gosho":"Nazuna Gosho","Nazuna_Kyoto_Nijojo":"Nazuna Nijo-jo","Four_Seasons_Hotel_Kyoto":"Four Seasons Kyoto","Hyatt_Regency_Kyoto":"Hyatt Regency Kyoto","Park_Hyatt_Kyoto":"Park Hyatt Kyoto","The_Junei_Hotel":"The Junei Hotel"}
df=pd.concat([pd.read_csv(f) for f in sorted(glob.glob(U+"reviews_*.csv"))],ignore_index=True); df["review_id"]=np.arange(len(df))
df["type"]=df["Location Name"].map(TIER); df["property"]=df["Location Name"].map(NAME)
s=pd.read_pickle("sent.pkl")
A={"staff_service":"Staff & service","room":"Room","dining":"Dining","location":"Location","culture":"Culture","bath":"Bath","value_price":"Value & price"}
# properties
g=df.groupby(["property","type"]).Rating
P=g.agg(n="size",mean="mean",sd="std").reset_index(); P["se"]=P.sd/np.sqrt(P.n); P["ci_lo"]=P["mean"]-1.96*P.se; P["ci_hi"]=(P["mean"]+1.96*P.se).clip(upper=5)
P["low_share"]=df.groupby("property").Rating.apply(lambda x:(x<=3).mean()*100).reindex(P.property).values
P=P.sort_values("mean",ascending=False)[["property","type","n","mean","ci_lo","ci_hi","sd","low_share"]]
for c in ["mean","ci_lo","ci_hi","sd"]: P[c]=P[c].round(3)
P["low_share"]=P.low_share.round(1); P.to_csv("properties.csv",index=False); print(P.to_string())
# anova table (numbers from anova.py output)
an=pd.DataFrame([
 ["oneway","One-way ANOVA, reviews as independent","Ryokan vs Hotel","149.84","1, 5586","< 0.001","2.6%","Significant"],
 ["welch","Welch ANOVA (unequal variances)","Ryokan vs Hotel","194.66","1, 5462","< 0.001","","Significant"],
 ["kruskal","Kruskal-Wallis (rank-based; H statistic)","Ryokan vs Hotel","153.10","1","< 0.001","","Significant"],
 ["threeway","One-way ANOVA, three types","Ryokan, Hotel, Hybrid","101.81","2, 6039","< 0.001","3.3%","Significant"],
 ["nested","Nested ANOVA, type tested against properties","Ryokan vs Hotel","6.30","1, 5","0.054","2.6%","Not significant"],
 ["propwithin","Properties within type","7 properties","24.27","5, 5581","< 0.001","2.1%","Significant"],
 ["interaction","Two-way ANOVA, type x peak season (interaction)","Ryokan vs Hotel","3.94","1, 5584","0.047","","Significant at review level only"],
],columns=["test","label","groups","F","df","p","eta2","verdict"]); an.to_csv("anova.csv",index=False)
# aspect heat
rows=[]
for a,lab in A.items():
    x=s[s["asp_"+a]==1].groupby("review_id").agg(v=("vader","mean"),b=("bert","mean"))
    d=df.join(x,on="review_id")
    for (p,t),gg in d.groupby(["property","type"]):
        m=gg.v.notna(); rows.append([p,t,lab,round(m.mean()*100,1),round((gg.v[m]>=.05).mean()*100,1),round((gg.v[m]<=-.05).mean()*100,1),int(m.sum())])
H=pd.DataFrame(rows,columns=["property","type","aspect","mention_share","positive_share","negative_share","n_mentions"]); H.to_csv("aspects.csv",index=False)
print(H.pivot(index="property",columns="aspect",values="mention_share").round(0).to_string())
# narrative arc: reviews with >=5 sentences, quintile position
s2=s.merge(df[["review_id","type"]],on="review_id"); s2["i"]=s2.groupby("review_id").cumcount(); s2["n"]=s2.groupby("review_id").review_id.transform("size")
s3=s2[s2.n>=5].copy(); s3["pos"]=np.minimum((s3.i/s3.n*5).astype(int),4)+1
r=s3.groupby(["review_id","type","pos"])[["vader","bert"]].mean().reset_index()
arc=r.groupby(["type","pos"]).agg(vader=("vader","mean"),bert=("bert","mean"),n_reviews=("review_id","nunique")).reset_index()
arc=arc.melt(id_vars=["type","pos","n_reviews"],var_name="measure",value_name="sentiment"); arc["sentiment"]=arc.sentiment.round(3)
arc["part"]=arc.pos.map({1:"Opening",2:"Early",3:"Middle",4:"Late",5:"Closing"}); arc.to_csv("arc.csv",index=False)
print(arc.pivot_table(index=["measure","type"],columns="pos",values="sentiment").to_string()); print(arc.groupby("type").n_reviews.first().to_dict())
# test: closing vs middle difference by type (paired)
w=r.pivot_table(index=["review_id","type"],columns="pos",values="vader").reset_index()
for t,gg in w.groupby("type"): print(t,"closing-middle VADER %.3f, t-test p=%.2g; opening-middle %.3f"%((gg[5]-gg[3]).mean(), stats.ttest_rel(gg[5],gg[3],nan_policy="omit").pvalue,(gg[1]-gg[3]).mean()))
# complaints: among <=3 star reviews, share with a negative mention (VADER) of each aspect; and lift vs 4-5 star
rows=[]
for a,lab in A.items():
    x=s[s["asp_"+a]==1].groupby("review_id").vader.mean(); d=df.join(x.rename("v"),on="review_id"); d["neg"]=(d.v<=-.05)
    for t in ["Ryokan","Hotel"]:
        lo=d[(d.type==t)&(d.Rating<=3)]; hi=d[(d.type==t)&(d.Rating>=4)]
        rows.append([t,lab,round(lo.neg.mean()*100,1),round(hi.neg.mean()*100,1),len(lo)])
C=pd.DataFrame(rows,columns=["type","aspect","low_rated_share","high_rated_share","n_low_rated"]); C.to_csv("complaints.csv",index=False); print(C.to_string())
