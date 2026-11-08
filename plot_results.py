"""Make a 4-panel figure from the CSVs.  Example: python plot_results.py results"""

import os
import sys

import matplotlib

matplotlib.use("Agg")  # draw to a file, no screen needed on a cluster
import matplotlib.pyplot as plt
import pandas as pd

outdir = sys.argv[1] if len(sys.argv) > 1 else "results"
summary = pd.read_csv(os.path.join(outdir, "summary.csv"))
sample = pd.read_csv(os.path.join(outdir, "annual_sample.csv"))
profile = pd.read_csv(os.path.join(outdir, "daily_profile.csv"), index_col="day")

fig, ax = plt.subplots(2, 2, figsize=(11, 8))

# (a) distribution of yearly rainfall for each clustering level
for p_ww, group in sample.groupby("p_wet_wet"):
    ax[0, 0].hist(group["total_mm"], bins=40, histtype="step", density=True,
                  label=f"p_wet_wet={p_ww}")
ax[0, 0].set(title="Annual rainfall", xlabel="mm per year", ylabel="density")
ax[0, 0].legend()

# (b) chance of a drought year
ax[0, 1].bar(summary["p_wet_wet"].astype(str), summary["drought_prob"])
ax[0, 1].set(title="Chance of a drought year", xlabel="p_wet_wet", ylabel="probability")

# (c) longest dry spell
ax[1, 0].plot(summary["p_wet_wet"], summary["mean_longest_dry"], "o-", label="mean")
ax[1, 0].plot(summary["p_wet_wet"], summary["p99_longest_dry"], "s--", label="99th percentile")
ax[1, 0].set(title="Longest dry spell in a year", xlabel="p_wet_wet", ylabel="days")
ax[1, 0].legend()

# (d) seasonal cycle (smoothed with a 15-day rolling mean)
profile.iloc[:, [0]].rolling(15, center=True, min_periods=1).mean().plot(ax=ax[1, 1], legend=False)
ax[1, 1].set(title="Average rain by day of year", xlabel="day of year", ylabel="mm/day")

fig.tight_layout()
fig.savefig(os.path.join(outdir, "summary.png"), dpi=120)
print("wrote", os.path.join(outdir, "summary.png"))
