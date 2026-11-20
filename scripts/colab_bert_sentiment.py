# Colab: run each block as its own cell (Runtime > Change runtime type > GPU).
# Upload the ten reviews_*.csv files (or a folder) to /content/reviews/ first.

# ---- Cell 1: install
# !pip install -q transformers torch pandas scikit-learn textblob

# ---- Cell 2: load raw data, tag type, split into sentences
import glob, re, numpy as np, pandas as pd
TYPE = {"Kyokoyado_Muromachi_Yutone": "Ryokan", "NISHIYAMA_RYOKAN": "Ryokan", "Ryokufuso": "Ryokan",
        "Shiraume": "Ryokan", "Nazuna_Kyoto_Gosho": "Ryokan", "Nazuna_Kyoto_Nijojo": "Ryokan",
        "Four_Seasons_Hotel_Kyoto": "Hotel", "Hyatt_Regency_Kyoto": "Hotel", "Park_Hyatt_Kyoto": "Hotel",
        "The_Junei_Hotel": "Boutique"}
df = pd.concat([pd.read_csv(f) for f in sorted(glob.glob("/content/reviews/reviews_*.csv"))], ignore_index=True)
df["review_id"] = np.arange(len(df)); df["type"] = df["Location Name"].map(TYPE)
split = lambda t: [s.strip() for s in re.split(r"(?<=[.!?])\s+|\n+", str(t)) if len(s.strip()) > 2]
sent = df[["review_id", "Text"]].assign(sentence=df.Text.map(split)).explode("sentence").dropna(subset=["sentence"])
print(len(df), "reviews ->", len(sent), "sentences")

# ---- Cell 3: BERT-family model, sentence level (name the model exactly in Chapter 3)
import torch
from transformers import pipeline
MODEL = "distilbert-base-uncased-finetuned-sst-2-english"   # DistilBERT fine-tuned on SST-2
clf = pipeline("sentiment-analysis", model=MODEL, device=0 if torch.cuda.is_available() else -1,
               truncation=True, max_length=128)
res = clf(sent.sentence.tolist(), batch_size=64)
sent["bert"] = [r["score"] if r["label"] == "POSITIVE" else -r["score"] for r in res]  # signed, -1..1

# ---- Cell 4: lexicon baseline (what the July draft actually used) + review-level aggregates
from textblob import TextBlob
sent["textblob"] = sent.sentence.map(lambda s: TextBlob(s).sentiment.polarity)
rev = sent.groupby("review_id").agg(bert_mean=("bert", "mean"), bert_min=("bert", "min"),
                                    tb_mean=("textblob", "mean")).reset_index()
out = df.merge(rev, on="review_id")
out.to_csv("reviews_with_sentiment.csv", index=False)
print(out.groupby("type")[["bert_mean", "tb_mean"]].mean().round(3))


# ---- Cell 4b: pre-specified aspect dictionary (fixed BEFORE looking at results) + sentence-level aspect sentiment
ASPECTS = {  # identical to phase3_extended_analyses.py
    "dining": r"kaiseki|breakfast|dinner|lunch|\bmeals?\b|\bfood\b|\bcourses?\b|matcha|tofu|restaurant|menu|\bchef|\bsake\b|cuisine",
    "bath": r"onsen|\bbath(?!room)|bathing|hot spring|\bsoak|yukata|sauna|\bspa\b|\bpool\b|ofuro|rotenburo|hinoki",
    "room": r"\brooms?\b|\bbeds?\b|futon|tatami|pillow|shower|toilet|bathroom|noise|noisy|\bview|spacious|decor|\bclean",
    "staff_service": r"\bstaff|service|hospitalit|welcom|attentive|helpful|friendly|concierge|\bowner|okami|\bhost|omotenashi|check.?in|check.?out|reception|\bmanager",
    "location": r"location|located|\bwalk|station|\bbus\b|taxi|subway|\btrain|distance|temple|\bgion\b|shrine|\bstreet|alley|neighbo",
    "value_price": r"\bprice|\bvalue\b|\bcost|expensive|\bworth|\bmoney\b|\brate\b|\bfees?\b|pricey|overpriced|cheap|afford",
    "culture": r"tradition|authentic|cultur|garden|atmospher|ambien|historic|machiya|kimono|ceremony|japanese style|heritage",
}
low = sent.sentence.str.lower()
for a, rx in ASPECTS.items():
    sent["asp_" + a] = low.str.contains(rx, regex=True).astype(int)
sent.to_csv("sentences_scored.csv", index=False)      # <- send me this file and reviews_with_sentiment.csv
print({a: int(sent["asp_" + a].sum()) for a in ASPECTS}, "sentences tagged per aspect")

# ---- Cell 5: build the hand-labeling sample (about 300 sentences, stratified by type)
rng = np.random.RandomState(42)
lab = sent.merge(df[["review_id", "type"]], on="review_id")
lab = lab[lab.type != "Boutique"].groupby("type", group_keys=False).apply(lambda g: g.sample(150, random_state=42))
lab[["review_id", "type", "sentence"]].assign(human_label="").to_csv("labeling_sample.csv", index=False)
# Open labeling_sample.csv, fill human_label with one of: pos / neu / neg  (about 2 hours). Do not look at model scores.

# ---- Cell 6: after labeling, upload labeling_sample.csv (filled) and evaluate both methods
from sklearn.metrics import f1_score, cohen_kappa_score, classification_report
lab2 = pd.read_csv("labeling_sample.csv").merge(sent[["review_id", "sentence", "bert", "textblob"]],
                                                 on=["review_id", "sentence"], how="left").drop_duplicates(["review_id", "sentence"])
cat = lambda x, t=0.05: np.where(x > t, "pos", np.where(x < -t, "neg", "neu"))
for name in ["bert", "textblob"]:
    pred = cat(lab2[name].values)
    print(name, "macro-F1 =", round(f1_score(lab2.human_label, pred, average="macro"), 3),
          "| kappa =", round(cohen_kappa_score(lab2.human_label, pred), 3))
print(classification_report(lab2.human_label, cat(lab2["bert"].values)))
