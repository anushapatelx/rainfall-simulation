"""
I used Claude (2026) on 11/08/2026 to write tests for rainism.py
"""

"""Tests for rainsim. Small inputs so the whole file runs in a few seconds."""

import numpy as np
import pandas as pd
import pytest

from rainsim import (
    DAYS_PER_YEAR,
    dry_to_wet_for_fraction,
    run_scenarios,
    seasonal_p_dry_wet,
    simulate_years,
    summarize,
)


# ---------------------------------------------------- dry_to_wet_for_fraction
def test_dry_to_wet_gives_requested_long_run_wet_fraction():
    p_ww = 0.6
    p_dw = dry_to_wet_for_fraction(0.4, p_ww)
    assert p_dw == pytest.approx(0.4 * 0.4 / 0.6)
    # plug back into the two-state formula: we must get 0.4 again
    assert p_dw / (1 - p_ww + p_dw) == pytest.approx(0.4)


def test_dry_to_wet_rejects_bad_input():
    with pytest.raises(ValueError):
        dry_to_wet_for_fraction(0.0, 0.5)
    with pytest.raises(ValueError):
        dry_to_wet_for_fraction(0.4, 1.5)
    with pytest.raises(ValueError):
        dry_to_wet_for_fraction(0.9, 0.0)  # would need a probability above 1


# ------------------------------------------------------ seasonal_p_dry_wet
def test_seasonal_peak_trough_and_no_seasonality():
    base = 0.3
    peak = seasonal_p_dry_wet(150, base, 0.5, 150)
    trough = seasonal_p_dry_wet(150 + 182, base, 0.5, 150)  # about half a year later
    assert peak == pytest.approx(base * 1.5)
    assert trough == pytest.approx(base * 0.5, rel=0.01)
    assert seasonal_p_dry_wet(77, base, 0.0, 150) == pytest.approx(base)


def test_seasonal_probability_is_clipped_to_valid_range():
    assert seasonal_p_dry_wet(150, 0.9, 0.5, 150) == 1.0
    assert seasonal_p_dry_wet(0, 0.0, 0.5, 150) == 0.0


# --------------------------------------------------------- simulate_years
def test_never_wet_gives_no_rain_and_full_year_dry_spell():
    annual, daily_mean = simulate_years(50, p_dry_wet=0.0, p_wet_wet=0.5, seed=1)
    assert (annual["total_mm"] == 0).all()
    assert (annual["wet_days"] == 0).all()
    assert (annual["longest_dry_spell"] == DAYS_PER_YEAR).all()
    assert (daily_mean == 0).all()


def test_always_wet_rains_every_day_with_no_dry_spell():
    annual, _ = simulate_years(50, p_dry_wet=1.0, p_wet_wet=1.0, seasonality=0.0, seed=1)
    assert (annual["wet_days"] == DAYS_PER_YEAR).all()
    assert (annual["longest_dry_spell"] == 0).all()
    assert (annual["total_mm"] > 0).all()


def test_average_wet_days_matches_theory():
    p_ww, p_dw = 0.6, 0.25
    annual, _ = simulate_years(20_000, p_dw, p_ww, seasonality=0.0, seed=2)
    wet_fraction = p_dw / (1 - p_ww + p_dw)          # = 0.3846...
    assert annual["wet_days"].mean() == pytest.approx(DAYS_PER_YEAR * wet_fraction, abs=1.5)


def test_average_total_rain_matches_wet_days_times_mean_amount():
    shape, scale = 0.8, 8.0
    annual, _ = simulate_years(20_000, 0.25, 0.6, shape=shape, scale=scale,
                               seasonality=0.0, seed=3)
    expected = annual["wet_days"].mean() * shape * scale   # gamma mean = shape * scale
    assert annual["total_mm"].mean() == pytest.approx(expected, rel=0.02)


def test_columns_are_consistent_with_each_other():
    annual, _ = simulate_years(500, 0.25, 0.6, seed=4)
    assert list(annual.columns) == ["total_mm", "wet_days", "max_day_mm", "longest_dry_spell"]
    assert len(annual) == 500
    assert (annual["max_day_mm"] <= annual["total_mm"]).all()
    assert annual["wet_days"].between(0, DAYS_PER_YEAR).all()
    assert annual["longest_dry_spell"].between(0, DAYS_PER_YEAR).all()
    # a year with no wet days has no rain; a year with rain has at least one wet day
    assert ((annual["total_mm"] > 0) == (annual["wet_days"] > 0)).all()


def test_clustering_makes_years_more_variable_with_longer_dry_spells():
    # same long-run wet fraction (0.4), different clustering
    loose, _ = simulate_years(10_000, dry_to_wet_for_fraction(0.4, 0.3), 0.3, seed=5)
    clustered, _ = simulate_years(10_000, dry_to_wet_for_fraction(0.4, 0.8), 0.8, seed=5)
    assert clustered["total_mm"].mean() == pytest.approx(loose["total_mm"].mean(), rel=0.05)
    assert clustered["total_mm"].std() > loose["total_mm"].std()
    assert clustered["longest_dry_spell"].mean() > loose["longest_dry_spell"].mean()


def test_seasonal_cycle_peaks_near_peak_day():
    _, daily_mean = simulate_years(20_000, 0.25, 0.6, seasonality=0.6, peak_day=100, seed=6)
    near_peak = daily_mean[95:106].mean()
    near_trough = daily_mean[(100 + 182 - 5):(100 + 182 + 6)].mean()
    assert near_peak > 1.5 * near_trough


def test_same_seed_is_reproducible_and_different_seed_differs():
    a, _ = simulate_years(200, 0.25, 0.6, seed=7)
    b, _ = simulate_years(200, 0.25, 0.6, seed=7)
    c, _ = simulate_years(200, 0.25, 0.6, seed=8)
    pd.testing.assert_frame_equal(a, b)
    assert not a["total_mm"].equals(c["total_mm"])


def test_simulate_years_rejects_bad_input():
    with pytest.raises(ValueError):
        simulate_years(0, 0.25, 0.6)
    with pytest.raises(ValueError):
        simulate_years(10, 1.2, 0.6)
    with pytest.raises(ValueError):
        simulate_years(10, 0.25, 0.6, shape=-1.0)


# ------------------------------------------------------------- summarize
def test_summarize_on_a_hand_made_table():
    annual = pd.DataFrame({
        "total_mm": [100.0, 200.0, 300.0, 400.0],
        "wet_days": [1, 2, 3, 4],
        "max_day_mm": [10.0, 20.0, 30.0, 40.0],
        "longest_dry_spell": [10, 20, 30, 40],
    })
    s = summarize(annual, drought_mm=250.0)
    assert s["mean_total_mm"] == pytest.approx(250.0)
    assert s["std_total_mm"] == pytest.approx(np.std([100, 200, 300, 400], ddof=1))
    assert s["drought_prob"] == pytest.approx(0.5)   # 100 and 200 are below 250
    assert s["mean_longest_dry"] == pytest.approx(25.0)
    assert s["p99_longest_dry"] == pytest.approx(np.quantile([10, 20, 30, 40], 0.99))


# --------------------------------------------------------- run_scenarios
def test_run_scenarios_shapes_and_drought_risk_rises_with_clustering():
    p_values = [0.3, 0.6, 0.85]
    summary, sample, profile = run_scenarios(p_values, n_years=4000, sample_years=100,
                                             drought_mm=700.0, seed=0)
    assert list(summary["p_wet_wet"]) == p_values
    assert len(sample) == 100 * len(p_values)
    assert profile.shape == (DAYS_PER_YEAR, len(p_values))
    # same average rain in every scenario (within 5%) ...
    assert summary["mean_total_mm"].max() / summary["mean_total_mm"].min() < 1.05
    # ... but more drought risk and longer dry spells when rain is clustered
    assert summary["drought_prob"].is_monotonic_increasing
    assert summary["mean_longest_dry"].is_monotonic_increasing
