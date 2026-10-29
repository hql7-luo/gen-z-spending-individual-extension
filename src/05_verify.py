"""Independently verify headline, accounting, preference and publication checks."""

# Import tools for independent calculations and publication checks.
from pathlib import Path
import hashlib
import json
import math

import numpy as np
import pandas as pd
from scipy.stats import chi2

# Read the recovered financial source and its published aggregate tables.
ROOT = Path(__file__).resolve().parents[1]
TABLES = ROOT / "outputs/tables"
source = ROOT / "data/raw/genz_money_spends.csv"
assert hashlib.sha256(source.read_bytes()).hexdigest() == "7f11ed0fd2e95de43687d84ad6ee7d575b0c61f7a06d4522bffe15fb6c8dab41"
raw = pd.read_csv(source)
core = pd.read_csv(TABLES / "finance_core_metrics.csv").iloc[0]
categories = ["Rent", "Groceries", "Eating Out", "Entertainment", "Subscription Services",
              "Education", "Online Shopping", "Travel", "Fitness", "Miscellaneous"]
spend = raw[[name + " (USD)" for name in categories]].sum(axis=1)
income = raw["Income (USD)"]
assert raw.shape == (1700, 15) and not raw.isna().any().any()
assert int((spend > income).sum()) == int(core["consumption_above_income_count"]) == 860
assert int((spend == income).sum()) == 0
np.testing.assert_allclose(income.corr(spend), core["income_consumption_pearson_r"], atol=1e-12)
np.testing.assert_allclose((spend > income).mean() * 100, core["consumption_above_income_pct"], atol=1e-10)

# Recheck group membership independently of the SQL group labels.
profiles = pd.read_csv(TABLES / "finance_segments.csv").set_index("segment")
assert len(profiles) == 4 and profiles.n.sum() == len(raw)
for segment, row in profiles.iterrows():
    lower = income < income.median()
    above = spend > income
    mask = (lower if segment.startswith("lower") else ~lower)
    mask &= (~above if "not_above" in segment else above)
    assert int(mask.sum()) == int(row.n)
    np.testing.assert_allclose(spend[mask].mean(), row.consumption_mean, atol=1e-8)
shares = pd.read_csv(TABLES / "finance_category_shares.csv")
np.testing.assert_allclose(shares.groupby("segment").aggregate_consumption_share_pct.sum(), 100, atol=1e-9)
actions = pd.read_csv(TABLES / "marketing_actions.csv")
assert set(actions.segment) == set(profiles.index)
assert actions.n.sum() == len(raw)

# Recalculate chi-square statistics directly from the public counts, without the raw shopping CSV.
tests = pd.read_csv(TABLES / "shopping_tests.csv").set_index("preference")
p_values = []
test_names = ["payment", "shipping", "frequency", "category"]
for name in test_names:
    counts = pd.read_csv(TABLES / f"shopping_{name}_counts.csv", index_col=0).to_numpy().T
    assert counts.shape[0] == 2 and counts.sum() == 3900
    assert list(counts.sum(axis=1)) == [723, 3177]
    expected = counts.sum(axis=1)[:, None] * counts.sum(axis=0)[None, :] / counts.sum()
    statistic = ((counts - expected) ** 2 / expected).sum()
    degrees = (counts.shape[0] - 1) * (counts.shape[1] - 1)
    p_value = chi2.sf(statistic, degrees)
    effect = math.sqrt(statistic / (counts.sum() * min(counts.shape[0] - 1, counts.shape[1] - 1)))
    np.testing.assert_allclose([statistic, degrees, expected.min(), p_value, effect],
        tests.loc[name, ["chi_square", "degrees_freedom", "minimum_expected_count", "p_raw", "cramers_v"]].astype(float), atol=1e-10)
    assert expected.min() >= 5
    p_values.append(p_value)

# Use a vectorized Holm calculation, separate from the shopping script's loop.
p_values = np.array(p_values)
order = np.argsort(p_values)
adjusted = np.empty(len(order))
adjusted[order] = np.minimum(1, np.maximum.accumulate(p_values[order] * np.arange(len(order), 0, -1)))
np.testing.assert_allclose(adjusted, tests.loc[test_names, "p_holm"], atol=1e-10)
assert (adjusted >= 0.05).all()

# Check that the repository keeps material caveats and excludes private course material.
readme = (ROOT / "README.md").read_text()
for phrase in ["Individual Extension After the Course", "synthetic", "unspecified", "860 / 1,700", "29.82%"]:
    assert phrase in readme, f"Missing important README disclosure: {phrase}"
for folder in [ROOT / "src", ROOT / "sql", ROOT / "outputs"]:
    for path in folder.rglob("*"):
        if path.suffix in {".py", ".sql", ".md", ".csv", ".json"}:
            text = path.read_text()
            assert "\u2014" not in text, f"English em dash found in {path.relative_to(ROOT)}"
            assert ("/" + "Users/") not in text, f"Local private path found in {path.relative_to(ROOT)}"

# Print a bounded receipt only after all independent checks pass.
print(json.dumps({"financial_rows": len(raw), "shopping_aggregate_rows": 3900,
                  "rule_groups": len(profiles), "preference_tests": len(test_names),
                  "independent_checks_passed": True}, indent=2))
