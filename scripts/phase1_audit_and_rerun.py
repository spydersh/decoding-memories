"""
Phase 1: data audit + corrected rerun of the rating and seasonality analyses.
Run:  python phase1_audit_and_rerun.py <folder with reviews_*.csv>
Needs: pandas numpy scipy statsmodels vaderSentiment
Writes: phase1_results.md next to the script.
NOTE: sentiment here is VADER (lexicon baseline). BERT scores must be added in Colab.
"""
import sys, glob, os, itertools, warnings
import numpy as np, pandas as pd
from scipy import stats
import statsmodels.formula.api as smf
warnings.filterwarnings("ignore")

DATA_DIR = sys.argv[1] if len(sys.argv) > 1 else "."
SEED = 42
np.random.seed(SEED)

TYPE = {  # classification that reproduces the July inferential sample (2,296 / 3,630 / 116)
    "Kyokoyado_Muromachi_Yutone": "Ryokan", "NISHIYAMA_RYOKAN": "Ryokan", "Ryokufuso": "Ryokan",
    "Shiraume": "Ryokan", "Nazuna_Kyoto_Gosho": "Ryokan", "Nazuna_Kyoto_Nijojo": "Ryokan",
    "Four_Seasons_Hotel_Kyoto": "Hotel", "Hyatt_Regency_Kyoto": "Hotel", "Park_Hyatt_Kyoto": "Hotel",
    "The_Junei_Hotel": "Boutique",
}
PEAK_MONTHS = [3, 4, 10, 11]  # as defined in the July draft (review month, not stay month)

out = []
def say(s=""):
    print(s); out.append(s)

df = pd.concat([pd.read_csv(f) for f in sorted(glob.glob(os.path.join(DATA_DIR, "reviews_*.csv")))], ignore_index=True)
df["prop"] = df["Location Name"]; df["type"] = df["prop"].map(TYPE)
df["date"] = pd.to_datetime(dict(year=df.Year, month=df.Month, day=df.Day))
df["five"] = (df.Rating == 5).astype(int)
df["era"] = pd.cut(df.Year, [2000, 2019, 2022, 2030], labels=["<=2019", "2020-22", "2023+"])
df["peak"] = df.Month.isin(PEAK_MONTHS).astype(int)
nonascii = df.Text.map(lambda s: sum(ord(c) > 127 for c in s) / max(len(s), 1))
df["likely_non_english"] = nonascii > 0.3

say("## 1. Audit")
say(f"- reviews: {len(df)}; properties: {df.prop.nunique()}; date range: {df.date.min().date()} to {df.date.max().date()}")
say(f"- missing text: {df.Text.isna().sum()}; exact duplicate texts: {df.duplicated('Text').sum()}")
say(f"- likely non-English (>30% non-ASCII): {int(df.likely_non_english.sum())}")
say(f"- reviews up to 2019: {(df.Year<=2019).sum()} ({(df.Year<=2019).mean():.0%})")
say("")
say(df.groupby(["type", "prop"]).agg(n=("Rating", "size"), mean=("Rating", "mean"), sd=("Rating", "std"),
    share5=("five", "mean"), first_year=("Year", "min")).round(3).to_markdown())

d = df[df.type != "Boutique"].copy()
r, h = d[d.type == "Ryokan"].Rating, d[d.type == "Hotel"].Rating
t = stats.ttest_ind(r, h, equal_var=False); sp = np.sqrt((r.var() + h.var()) / 2)
say("\n## 2. Review-level comparison (reproduces July Table 5)")
say(f"- Ryokan {r.mean():.3f} (n={len(r)}) vs Hotel {h.mean():.3f} (n={len(h)}); Welch t={t.statistic:.2f}; d={(r.mean()-h.mean())/sp:.3f}")

def perm(pm):
    vals, lab = pm.Rating.values, (pm.type == "Ryokan").values; k = lab.sum()
    obs = vals[lab].mean() - vals[~lab].mean(); diffs = []
    for c in itertools.combinations(range(len(vals)), k):
        m = np.zeros(len(vals), bool); m[list(c)] = True; diffs.append(vals[m].mean() - vals[~m].mean())
    diffs = np.array(diffs); return obs, float((np.abs(diffs) >= abs(obs) - 1e-12).mean()), len(diffs)

say("\n## 3. Property-level inference (property is the unit that matters)")
for label, dd in [("all 9 properties", d), ("excluding Nazuna", d[~d.prop.str.startswith("Nazuna")]),
                  ("reviews 2023+", d[d.Year >= 2023]), ("reviews <=2019", d[d.Year <= 2019])]:
    pm = dd.groupby(["prop", "type"]).Rating.mean().reset_index()
    obs, p, n = perm(pm)
    say(f"- {label}: gap = {obs:+.3f} stars, exact permutation p = {p:.3f} ({n} assignments)")
for label, dd in [("all 9", d), ("no Nazuna", d[~d.prop.str.startswith("Nazuna")])]:
    m = smf.mixedlm("Rating ~ C(type, Treatment('Hotel')) + C(era)", dd, groups=dd["prop"]).fit(reml=True)
    say(f"- mixed model ({label}, era-adjusted): type effect {m.params.iloc[1]:+.3f}, SE {m.bse.iloc[1]:.3f} "
        f"(few clusters: treat the p-value as optimistic)")

say("\n## 4. Seasonality (peak = Mar-Apr, Oct-Nov by REVIEW month)")
say(d.groupby(["type", "peak"]).Rating.agg(["size", "mean"]).round(3).to_markdown())
m3 = smf.mixedlm("Rating ~ C(type, Treatment('Hotel'))*peak + C(era)", d, groups=d["prop"]).fit(reml=True)
k = [i for i in m3.params.index if "peak" in i and ":" in i][0]
say(f"- hotel peak effect: {m3.params['peak']:+.3f} (95% CI {m3.params['peak']-1.96*m3.bse['peak']:+.3f}, {m3.params['peak']+1.96*m3.bse['peak']:+.3f})")
say(f"- ryokan x peak interaction: {m3.params[k]:+.3f} (95% CI {m3.params[k]-1.96*m3.bse[k]:+.3f}, {m3.params[k]+1.96*m3.bse[k]:+.3f})")
try:
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
    sia = SentimentIntensityAnalyzer(); d["vader"] = d.Text.map(lambda s: sia.polarity_scores(s)["compound"])
    m4 = smf.mixedlm("vader ~ C(type, Treatment('Hotel'))*peak + C(era)", d, groups=d["prop"]).fit(reml=True)
    k4 = [i for i in m4.params.index if "peak" in i and ":" in i][0]
    say(f"- VADER baseline (NOT BERT): interaction {m4.params[k4]:+.3f} (95% CI {m4.params[k4]-1.96*m4.bse[k4]:+.3f}, {m4.params[k4]+1.96*m4.bse[k4]:+.3f})")
except ImportError:
    say("- vaderSentiment not installed; skipped")

open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "phase1_results.md"), "w").write("\n".join(out))
