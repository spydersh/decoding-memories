import warnings, numpy as np, pandas as pd
import statsmodels.formula.api as smf
warnings.filterwarnings("ignore")
d = pd.read_csv("data/phase3_review_features.csv")
A = ["dining", "bath", "room", "staff_service", "location", "value_price", "culture"]
d["log_words"] = np.log(d.n_words.clip(lower=1)); core = d[d.tier.isin(["Ryokan", "Hotel"])].copy()
base = "Rating ~ " + " + ".join(f"pos_{a} + neg_{a}" for a in A) + " + log_words + C(prop)"
def rewards(sub):
    m = smf.ols(base, data=sub).fit(cov_type="HC3")
    return {a: m.params["pos_" + a] for a in A}
r = rewards(core); print("all:", {k: round(v, 3) for k, v in sorted(r.items(), key=lambda x: -x[1])})
for pr in core.prop.unique():
    r = rewards(core[core.prop != pr]); top = sorted(r.items(), key=lambda x: -x[1])
    print(f"without {pr:28s} top: {top[0][0]} {top[0][1]:+.3f} | second: {top[1][0]} {top[1][1]:+.3f}")
for t in ["Ryokan", "Hotel"]:
    r = rewards(core[core.tier == t]); top = sorted(r.items(), key=lambda x: -x[1]); print(t, [(k, round(v, 3)) for k, v in top[:3]])
