"""
I used Claude (2026) on 11/08/2026 to write this code. I went through the code to undestand
how the different functions are working and assessing if the calculations are correctly written
"""

"""Simple daily rainfall simulator.

Question: if two places get the same AVERAGE rainfall, but in one place rainy
days come in clusters (wet days tend to follow wet days), how much more risk
of drought years and long dry spells does the clustered place have?

Model (a "two-state Markov chain" plus a gamma distribution):
  1. Each day is either WET or DRY.
  2. If yesterday was dry, today is wet with probability p_dry_wet.
     If yesterday was wet, today is wet with probability p_wet_wet.
     (A big p_wet_wet means rain comes in clusters.)
  3. p_dry_wet follows a seasonal cosine wave (+/- a percentage of its average),
     so some times of year are rainier.
  4. On a wet day, the amount of rain (mm) is drawn from a gamma distribution
     (lots of light rain, a few heavy storms).

We simulate many years at once: every array below has one entry per simulated year.
"""

import numpy as np
import pandas as pd

DAYS_PER_YEAR = 365


def dry_to_wet_for_fraction(wet_fraction, p_wet_wet):
    """Find p_dry_wet that gives a chosen long-run fraction of wet days.

    In the long run a two-state chain is wet a fraction
        wet_fraction = p_dry_wet / (1 - p_wet_wet + p_dry_wet)
    of the time. Solving that for p_dry_wet gives the formula below.
    This lets us change the clustering (p_wet_wet) while keeping the
    number of rainy days the same.
    """
    if not 0 < wet_fraction < 1:
        raise ValueError("wet_fraction must be between 0 and 1")
    if not 0 <= p_wet_wet <= 1:
        raise ValueError("p_wet_wet must be between 0 and 1")
    p = wet_fraction * (1 - p_wet_wet) / (1 - wet_fraction)
    if p > 1:
        raise ValueError("this wet_fraction and p_wet_wet need p_dry_wet > 1")
    return p


def seasonal_p_dry_wet(day, base, seasonality, peak_day):
    """Chance of a dry day turning wet, on a given day of the year (0-364).

    A cosine wave: highest on peak_day, lowest half a year later.
    seasonality is the size of the swing as a fraction of base
    (0.3 means +/- 30%). np.clip keeps the result between 0 and 1.
    """
    wave = np.cos(2 * np.pi * (day - peak_day) / DAYS_PER_YEAR)
    return float(np.clip(base * (1 + seasonality * wave), 0.0, 1.0))


def simulate_years(n_years, p_dry_wet, p_wet_wet, shape=0.8, scale=8.0,
                   seasonality=0.3, peak_day=150, seed=0):
    """Simulate n_years of daily rainfall.

    Returns
    -------
    annual : DataFrame with one row per year and columns
        total_mm, wet_days, max_day_mm, longest_dry_spell
    daily_mean : array of 365 numbers, the average rain (mm) on each day of the year
    """
    if n_years < 1:
        raise ValueError("n_years must be at least 1")
    for p in (p_dry_wet, p_wet_wet):
        if not 0 <= p <= 1:
            raise ValueError("probabilities must be between 0 and 1")
    if shape <= 0 or scale <= 0:
        raise ValueError("shape and scale must be positive")

    rng = np.random.default_rng(seed)

    # running totals, one entry per simulated year
    is_wet = np.zeros(n_years, dtype=bool)   # every year starts on a dry day
    total = np.zeros(n_years)                # total rain so far (mm)
    wet_days = np.zeros(n_years, dtype=int)  # number of wet days so far
    biggest = np.zeros(n_years)              # biggest one-day rain so far (mm)
    dry_run = np.zeros(n_years, dtype=int)   # current streak of dry days
    longest_dry = np.zeros(n_years, dtype=int)
    daily_mean = np.zeros(DAYS_PER_YEAR)

    for day in range(DAYS_PER_YEAR):
        p_dw = seasonal_p_dry_wet(day, p_dry_wet, seasonality, peak_day)
        # chance of rain today depends on whether yesterday was wet
        chance = np.where(is_wet, p_wet_wet, p_dw)
        is_wet = rng.random(n_years) < chance
        # rain amount: gamma draw on wet days, 0 on dry days
        rain = np.where(is_wet, rng.gamma(shape, scale, n_years), 0.0)

        total += rain
        wet_days += is_wet
        biggest = np.maximum(biggest, rain)
        dry_run = np.where(is_wet, 0, dry_run + 1)       # reset streak if wet
        longest_dry = np.maximum(longest_dry, dry_run)
        daily_mean[day] = rain.mean()

    annual = pd.DataFrame({
        "total_mm": total,
        "wet_days": wet_days,
        "max_day_mm": biggest,
        "longest_dry_spell": longest_dry,
    })
    return annual, daily_mean


def summarize(annual, drought_mm):
    """Boil a table of simulated years down to a few numbers (a dict).

    A "drought year" is a year with less than drought_mm of total rain.
    """
    return {
        "mean_total_mm": annual["total_mm"].mean(),
        "std_total_mm": annual["total_mm"].std(),
        "drought_prob": (annual["total_mm"] < drought_mm).mean(),
        "mean_longest_dry": annual["longest_dry_spell"].mean(),
        "p99_longest_dry": annual["longest_dry_spell"].quantile(0.99),
    }


def run_scenarios(p_wet_wet_values, wet_fraction=0.4, n_years=10_000,
                  shape=0.8, scale=8.0, drought_mm=700.0,
                  sample_years=1000, seed=0):
    """Run one simulation per p_wet_wet value (same average rain, different clustering).

    Returns three DataFrames: summary (one row per scenario),
    sample (the first sample_years simulated years of every scenario),
    and profile (average rain on each day of the year, one column per scenario).
    """
    summaries, samples, profile = [], [], {}
    for i, p_ww in enumerate(p_wet_wet_values):
        p_dw = dry_to_wet_for_fraction(wet_fraction, p_ww)
        annual, daily_mean = simulate_years(
            n_years, p_dw, p_ww, shape=shape, scale=scale, seed=seed + i)

        row = summarize(annual, drought_mm)
        row["p_wet_wet"] = p_ww
        summaries.append(row)
        samples.append(annual.head(sample_years).assign(p_wet_wet=p_ww))
        profile[f"p_wet_wet={p_ww}"] = daily_mean

    summary = pd.DataFrame(summaries)
    sample = pd.concat(samples, ignore_index=True)
    profile = pd.DataFrame(profile)
    profile.index.name = "day"
    return summary, sample, profile
