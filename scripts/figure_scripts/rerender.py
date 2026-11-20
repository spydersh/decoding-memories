import sys, runpy, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
S=float(sys.argv[1]); _orig=plt.subplots
def scaled(*a, **k):
    if "figsize" in k: k["figsize"]=(k["figsize"][0]*S, k["figsize"][1]*S)
    return _orig(*a, **k)
plt.subplots=scaled
sys.argv=["make_figures.py"]+sys.argv[2:]
runpy.run_path(__import__("os").path.join(__import__("os").path.dirname(__import__("os").path.abspath(__file__)), "make_figures.py"), run_name="__main__")
