import glob, re, itertools, numpy as np, pandas as pd, warnings
warnings.filterwarnings("ignore")
U=__import__("os").environ.get("DM_RAW","data_raw").rstrip("/")+"/"
TIER={"Kyokoyado_Muromachi_Yutone":"Ryokan","NISHIYAMA_RYOKAN":"Ryokan","Ryokufuso":"Ryokan","Shiraume":"Ryokan","Nazuna_Kyoto_Gosho":"Hybrid","Nazuna_Kyoto_Nijojo":"Hybrid","Four_Seasons_Hotel_Kyoto":"Hotel","Hyatt_Regency_Kyoto":"Hotel","Park_Hyatt_Kyoto":"Hotel","The_Junei_Hotel":"Hybrid"}
NAME={"Kyokoyado_Muromachi_Yutone":"Muromachi Yutone","NISHIYAMA_RYOKAN":"Nishiyama Ryokan","Ryokufuso":"Ryokufuso","Shiraume":"Shiraume","Nazuna_Kyoto_Gosho":"Nazuna Gosho","Nazuna_Kyoto_Nijojo":"Nazuna Nijo-jo","Four_Seasons_Hotel_Kyoto":"Four Seasons Kyoto","Hyatt_Regency_Kyoto":"Hyatt Regency Kyoto","Park_Hyatt_Kyoto":"Park Hyatt Kyoto","The_Junei_Hotel":"The Junei Hotel"}
A={"staff_service":"Staff & service","room":"Room","dining":"Dining","location":"Location","culture":"Culture","bath":"Bath","value_price":"Value & price"}
def load():
    df=pd.concat([pd.read_csv(f) for f in sorted(glob.glob(U+"reviews_*.csv"))],ignore_index=True); df["review_id"]=np.arange(len(df))
    df["type"]=df["Location Name"].map(TIER); df["property"]=df["Location Name"].map(NAME)
    df["peak"]=df.Month.isin([3,4,10,11]).astype(int); df["era"]=pd.cut(df.Year,[2000,2019,2022,2030],labels=["2005-2019","2020-2022","2023-2026"]).astype(str)
    df["log_words"]=np.log(df.Text.astype(str).str.split().str.len().clip(lower=1)); df["low"]=(df.Rating<=3).astype(int)
    s=pd.read_pickle("sent.pkl")
    return df,s
def feats(df,s,col):
    g=s.groupby("review_id"); rv=pd.DataFrame({"s_mean":g[col].mean()})
    for a in A: rv["sent_"+a]=s[s["asp_"+a]==1].groupby("review_id")[col].mean()
    d=df.join(rv,on="review_id")
    for a in A:
        d["mention_"+a]=d["sent_"+a].notna().astype(int); d["pos_"+a]=(d["sent_"+a]>=.05).astype(int); d["neg_"+a]=(d["sent_"+a]<=-.05).astype(int)
    return d
