from common import *
from sklearn.feature_extraction.text import CountVectorizer, ENGLISH_STOP_WORDS
from sklearn.decomposition import LatentDirichletAllocation
p=pd.read_csv(U+"processed_reviews_all.csv")
T3={"Kyokoyado Muromachi Yutone":"Ryokan","Nishiyama Ryokan":"Ryokan","Ryokufuso":"Ryokan","Shiraume":"Ryokan","Four Seasons Hotl Kyoto":"Hotel","Hyatt Regency Kyoto":"Hotel","Parkhyatt":"Hotel","Nazuna Kyoto Gosho":"Hybrid","Nazuna Kyoto Nijojo":"Hybrid","Junei Hotel Kyoto":"Hybrid"}
d=p.copy(); d["Location Name"]=d.Hotel_Name; d["type"]=d.Hotel_Name.map(T3); d["era"]=pd.cut(d.Year,[2000,2019,2022,2030],labels=["2005-2019","2020-2022","2023-2026"]).astype(str)
# ---------- topics (same procedure as phase 2, k = 5)
import nltk; nltk.download("wordnet",quiet=True)
from nltk.stem import WordNetLemmatizer
from functools import lru_cache
lem=WordNetLemmatizer()
@lru_cache(maxsize=None)
def lemma(w): return lem.lemmatize(lem.lemmatize(w,"v"),"n")
NAMES=set("shiraume hyatt regency park four seasons nazuna junei nishiyama ryokufuso yutone kyokoyado muromachi gosho nijojo kyoto japan japanese hotel ryokan inn gion nijo shijo karasuma imperial palace".split())
STOP=set(ENGLISH_STOP_WORDS)|NAMES|set("nt didn don ve ll just really also got get went".split())
toks=lambda t:[w for w in [lemma(w) for w in re.findall(r"[a-z]{3,}",str(t).lower())] if w not in STOP and len(w)>2]
d["tokens"]=d.Text.map(toks)
tmp=d[["Location Name","tokens"]].explode("tokens").dropna(); dfc=tmp.groupby(["tokens","Location Name"]).size().unstack(fill_value=0)
drop=set(dfc.index[(dfc.sum(1)>=20)&(dfc.max(1)/dfc.sum(1)>0.6)]); d["tokens"]=d.tokens.map(lambda ws:[w for w in ws if w not in drop])
cv=CountVectorizer(analyzer=lambda x:x,min_df=10,max_df=0.5); X=cv.fit_transform(d.tokens); vocab=np.array(cv.get_feature_names_out())
lda=LatentDirichletAllocation(n_components=5,learning_method="batch",max_iter=50,random_state=42).fit(X); theta=lda.transform(X)
tw=[list(vocab[np.argsort(c)[::-1][:12]]) for c in lda.components_]
for i,w in enumerate(tw): print(i,", ".join(w))
th=pd.DataFrame(theta,columns=range(5)); th["type"]=d.type.values; th["era"]=d.era.values
print(th.groupby("type")[list(range(5))].mean().round(3).T.to_string())
th.to_pickle("theta.pkl"); pd.to_pickle(tw,"topwords.pkl")

LAB={0:"General praise",1:"Location and surroundings",2:"Memorable experience",3:"Traditional stay",4:"Transactions and problems"}
rows=[]
for k in range(5):
    for t in ["Ryokan","Hotel","Hybrid"]:
        g=th[th.type==t]; rows.append([k,LAB[k],", ".join(tw[k][:10]),t,"All years",len(g),round(g[k].mean()*100,1)])
        for e,gg in g.groupby("era"): rows.append([k,LAB[k],", ".join(tw[k][:10]),t,e,len(gg),round(gg[k].mean()*100,1)])
pd.DataFrame(rows,columns=["topic","label","top_words","type","period","n","share"]).to_csv("topics.csv",index=False)
