from common import *
from scipy import stats
import statsmodels.formula.api as smf
df,s=load(); d=feats(df,s,"vader")
PROP={"Shiraume":(35.0052348,135.7733233),"Muromachi Yutone":(34.998366,135.7575024),"Ryokufuso":(34.9945107,135.7554024),"Nishiyama Ryokan":(35.0131089,135.7662971),"Hyatt Regency Kyoto":(34.9882626,135.7728336),"Four Seasons Kyoto":(34.9902288,135.7761797),"Park Hyatt Kyoto":(34.9991121,135.7811268),"Nazuna Gosho":(35.0158832,135.7571696),"Nazuna Nijo-jo":(35.0147086,135.7534847),"The Junei Hotel":(35.0212696,135.7524325)}
HOT=[("Kiyomizu-dera","Gion / Kiyomizu",34.9946662,135.784661),("Yasaka Shrine (Gion)","Gion / Kiyomizu",35.0036559,135.7785534),("Fushimi Inari Taisha","Fushimi",34.9676945,135.7791876),("Togetsukyo Bridge (Arashiyama)","Saga / Arashiyama",35.0128769,135.6777748),("Kinkaku-ji","Kinugasa / Kitano / Nishijin",35.03937,135.7292431),("Ginkaku-ji","Philosopher's Path / Okazaki",35.0270213,135.7982058),("Heian Shrine","Philosopher's Path / Okazaki",35.0159823,135.7824263),("Nishiki Market","City centre",35.0050258,135.764723),("Kyoto Station","Kyoto Station area",34.985849,135.7587667),("Nijo Castle","City centre",35.0140379,135.7484258)]
def hav(a,b):
    R=6371000; p1,p2=np.radians(a[0]),np.radians(b[0]); dphi=p2-p1; dl=np.radians(b[1]-a[1])
    return 2*R*np.arcsin(np.sqrt(np.sin(dphi/2)**2+np.cos(p1)*np.cos(p2)*np.sin(dl/2)**2))
CROWD=r"\bcrowd|overcrowd|\bpacked\b|\bswarm|\bthrong|too many (?:people|tourists)|tour groups?|tour bus|bus ?loads?|\bqueue|long lines?|overtouris|touristy|\bbusy\b|\bhordes?\b|\bmasses\b"
REFUGE=r"away from|escape|far from|retreat|oasis|quiet|peaceful|tranquil|calm|respite|refuge|haven|sanctuary|avoid|without the crowd|no crowd|not crowded|less crowded|never crowded|wasn'?t crowded|beat the crowd|before the crowd|not (?:too |very |so |that |at all )?(?:crowded|busy|touristy)|n't (?:feel |felt |seem |too |very |that )*(?:crowded|busy|touristy)|without (?:any |the |many )?(?:crowds?|lines?|queues?|line up)|no (?:crowds?|queues?|lines?)|never (?:felt |feel |too )?(?:crowded|busy)|barely|few (?:people|tourists)|busy season|busy traveller|busy tourist days"
sl=s.sentence.astype(str).str.lower(); sl=sl.str.replace(r"busy (?:day|days|schedule|itinerary|trip|week|weeks|time|morning|afternoon|sightseeing|touring|holiday|vacation)|queued up|taxi queue|queue of taxis","",regex=True); s["crowd"]=sl.str.contains(CROWD); s["refuge"]=s.crowd&sl.str.contains(REFUGE); s["exposed"]=s.crowd&~s.refuge
rv=s.groupby("review_id").agg(crowd=("crowd","max"),refuge=("refuge","max"),exposed=("exposed","max")).astype(int)
d=d.join(rv,on="review_id")
print("crowd mention share overall %.3f; refuge %.3f; exposed %.3f; n crowd sentences %d"%(d.crowd.mean(),d.refuge.mean(),d.exposed.mean(),s.crowd.sum()))
pd.set_option("display.max_colwidth",170); print(s[s.exposed].sentence.sample(30,random_state=11).str[:150].to_string(index=False))
rows=[]
for p,(la,lo) in PROP.items():
    g=d[d.property==p]; dist={h[0]:hav((la,lo),(h[2],h[3])) for h in HOT}
    near=min(dist,key=dist.get); core=min(dist["Kiyomizu-dera"],dist["Yasaka Shrine (Gion)"])
    m=g.mention_location==1
    rows.append(dict(property=p,type=g.type.iloc[0],lat=la,lon=lo,n=len(g),mean=round(g.Rating.mean(),3),low_share=round(g.low.mean()*100,1),
      nearest_hotspot=near,dist_nearest_m=int(round(dist[near])),dist_gion_kiyomizu_m=int(round(core)),dist_station_m=int(round(dist["Kyoto Station"])),hotspots_within_1500m=sum(v<=1500 for v in dist.values()),
      location_mention=round(m.mean()*100,1),location_positive=round(g.pos_location[m].mean()*100,1),location_negative=round(g.neg_location[m].mean()*100,1),
      crowd_share=round(g.crowd.mean()*100,1),crowd_exposed=round(g.exposed.mean()*100,1),crowd_refuge=round(g.refuge.mean()*100,1),
      peak_mean=round(g.Rating[g.peak==1].mean(),3),offpeak_mean=round(g.Rating[g.peak==0].mean(),3),peak_effect=round(g.Rating[g.peak==1].mean()-g.Rating[g.peak==0].mean(),3)))
L=pd.DataFrame(rows); L.to_csv("locations.csv",index=False); print(L.drop(columns=["lat","lon"]).to_string())
pd.DataFrame(HOT,columns=["name","area","lat","lon"]).to_csv("hotspots.csv",index=False)
# correlations (n=10), permutation p
def sp(x,y):
    r=stats.spearmanr(x,y)[0]; rng=np.random.RandomState(0); k=0; N=20000; y=np.asarray(y)
    for _ in range(N): k+= abs(stats.spearmanr(x,rng.permutation(y))[0])>=abs(r)-1e-12
    return r,(k+1)/(N+1)
PRED={"dist_gion_kiyomizu_m":"Distance to Gion / Kiyomizu","dist_nearest_m":"Distance to nearest busy sight","dist_station_m":"Distance to Kyoto Station"}
OUT={"mean":"Mean rating","low_share":"Share rated three stars or fewer","location_positive":"Positive share of location mentions","location_negative":"Negative share of location mentions","crowd_exposed":"Reviews describing crowds","crowd_refuge":"Reviews describing a refuge from crowds","peak_effect":"Peak-season change in rating"}
T=[]
for pk,pl in PRED.items():
    for ok,ol in OUT.items():
        r,pv=sp(L[pk],L[ok]); T.append([pk,pl,ok,ol,10,round(r,2),round(pv,3)])
T=pd.DataFrame(T,columns=["predictor","predictor_label","outcome","outcome_label","n","spearman","p"]); T.to_csv("location_tests.csv",index=False); print(T.drop(columns=["predictor","outcome"]).to_string())
# type confound
print(L.groupby("type")[["dist_gion_kiyomizu_m","dist_nearest_m","dist_station_m"]].mean().round(0))
# crowd by type x season x era
rows=[]
for t,g in d.groupby("type"):
    for lab,gg in [("All months",g),("Peak months",g[g.peak==1]),("Other months",g[g.peak==0])]:
        rows.append(["season",t,lab,len(gg),round(gg.crowd.mean()*100,1),round(gg.exposed.mean()*100,1),round(gg.refuge.mean()*100,1),round(gg.Rating[gg.exposed==1].mean(),2) if gg.exposed.sum() else None,round(gg.Rating[gg.exposed==0].mean(),2)])
    for e,gg in g.groupby("era"):
        rows.append(["period",t,e,len(gg),round(gg.crowd.mean()*100,1),round(gg.exposed.mean()*100,1),round(gg.refuge.mean()*100,1),round(gg.Rating[gg.exposed==1].mean(),2) if gg.exposed.sum() else None,round(gg.Rating[gg.exposed==0].mean(),2)])
CR=pd.DataFrame(rows,columns=["split","type","group","n","crowd_share","exposed_share","refuge_share","rating_if_crowds","rating_if_none"]); CR.to_csv("crowd.csv",index=False); print(CR.to_string())
# models: crowd exposure and rating within property; peak x near-core
core=d[d.type!="Hybrid"]
m=smf.ols("Rating ~ exposed + refuge + log_words + C(property)",data=d).fit(cov_type="HC3"); print("within-property: exposed %.3f (p=%.2g), refuge %.3f (p=%.2g)"%(m.params.exposed,m.pvalues.exposed,m.params.refuge,m.pvalues.refuge))
m2=smf.logit("exposed ~ peak + C(property)",data=d).fit(disp=0); print("exposed ~ peak OR %.2f p=%.3f"%(np.exp(m2.params.peak),m2.pvalues.peak))
m3=smf.logit("exposed ~ C(era) + C(property)",data=d).fit(disp=0); print(np.exp(m3.params.filter(like="era")).round(2).to_dict(), m3.pvalues.filter(like="era").round(3).to_dict())
d["near"]=d.property.map(dict(zip(L.property,(L.dist_gion_kiyomizu_m<=1000).astype(int))))
m4=smf.mixedlm("Rating ~ peak*near",data=d,groups=d.property).fit(); print(m4.summary().tables[1])
print(L[["property","dist_gion_kiyomizu_m"]].assign(near=lambda x:x.dist_gion_kiyomizu_m<=1000).to_string())
d[["review_id","crowd","refuge","exposed"]].to_pickle("crowdflags.pkl")
