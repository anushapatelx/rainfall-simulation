"""
I used Claude (2026) on 11/08/2026 to write this code to run rainism.py
"""


"""Run the rainfall experiment and save CSV results.

Example:  python run_simulation.py --years 20000 --outdir results
"""

import argparse
import os
import time

from rainsim import run_scenarios


def main():
    p = argparse.ArgumentParser(description="Rainfall clustering experiment")
    p.add_argument("--years", type=int, default=20_000, help="simulated years per scenario")
    p.add_argument("--p-wet-wet", type=float, nargs="+", default=[0.3, 0.5, 0.7, 0.85],
                   help="chance a wet day is followed by a wet day (one scenario each)")
    p.add_argument("--wet-fraction", type=float, default=0.4, help="long-run fraction of wet days")
    p.add_argument("--drought-mm", type=float, default=700.0, help="a year below this is a drought")
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--outdir", default="results")
    args = p.parse_args()

    start = time.time()
    print(f"{len(args.p_wet_wet)} scenarios x {args.years} years", flush=True)
    summary, sample, profile = run_scenarios(
        args.p_wet_wet, wet_fraction=args.wet_fraction, n_years=args.years,
        drought_mm=args.drought_mm, seed=args.seed)

    os.makedirs(args.outdir, exist_ok=True)
    summary.to_csv(os.path.join(args.outdir, "summary.csv"), index=False)
    sample.to_csv(os.path.join(args.outdir, "annual_sample.csv"), index=False)
    profile.to_csv(os.path.join(args.outdir, "daily_profile.csv"))

    print(summary.round(3).to_string(index=False))
    print(f"done in {time.time() - start:.1f} s; wrote CSVs to {args.outdir}/", flush=True)


if __name__ == "__main__":
    main()
