"""Create English figures from the verified local analysis outputs."""

# Import plotting and table tools, using a display-free backend for CI.
import json
import os
from pathlib import Path
import tempfile

os.environ.setdefault("MPLCONFIGDIR", str(Path(tempfile.gettempdir()) / "genz-matplotlib"))
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
import numpy as np
import pandas as pd


# Keep colors and labels consistent across every figure.
ROOT = Path(__file__).resolve().parents[1]
TABLES = ROOT / "outputs/tables"
FIGURES = ROOT / "outputs/figures"
NAVY = "#17324D"
TEAL = "#217F80"
GRAY = "#8E9A9F"
WARM = "#F6F4EF"
plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 10,
    "axes.spines.top": False, "axes.spines.right": False,
    "axes.titleweight": "bold", "axes.labelcolor": NAVY,
    "text.color": NAVY, "xtick.color": NAVY, "ytick.color": NAVY,
    "figure.facecolor": "white", "savefig.facecolor": "white",
    "text.parse_math": False,
})


# Save a finished figure at a readable resolution and release its memory.
def save_figure(figure, filename):
    figure.savefig(FIGURES / filename, dpi=200, bbox_inches="tight")
    plt.close(figure)


# Plot source records while taking the displayed statistics from verified tables.
def plot_income_consumption(core, finance):
    source = pd.read_csv(ROOT / finance["source_file"])
    consumption_columns = [
        "Rent (USD)", "Groceries (USD)", "Eating Out (USD)",
        "Entertainment (USD)", "Subscription Services (USD)", "Education (USD)",
        "Online Shopping (USD)", "Travel (USD)", "Fitness (USD)",
        "Miscellaneous (USD)",
    ]
    consumption = source[consumption_columns].sum(axis=1)
    if len(source) != int(core.n_included):
        raise ValueError("Source row count differs from the verified finance table.")
    figure, axis = plt.subplots(figsize=(9.2, 6.5))
    axis.scatter(source["Income (USD)"], consumption, s=13, alpha=0.27,
                 color=TEAL, edgecolors="none", rasterized=True)
    limit = max(source["Income (USD)"].max(), consumption.max()) * 1.04
    axis.plot([0, limit], [0, limit], color=GRAY, linewidth=1.3,
              linestyle="--", label="Consumption = income")
    axis.axvline(core.income_median, color=NAVY, linewidth=1,
                 linestyle=":", label=f"Sample income median: ${core.income_median:,.0f}")
    axis.set(xlim=(0, limit), ylim=(0, limit),
             xlabel="Income (USD)",
             ylabel="Consumption (USD)",
             title="Income and consumption look unrelated in this file")
    axis.xaxis.set_major_formatter(FuncFormatter(lambda value, position: f"{value:,.0f}"))
    axis.yaxis.set_major_formatter(FuncFormatter(lambda value, position: f"{value:,.0f}"))
    axis.text(0.03, 0.96,
              f"n = {int(core.n_included):,} | Ages {int(core.age_min)}-{int(core.age_max)}\n"
              f"Pearson r = {core.income_consumption_pearson_r:.2f}\n"
              f"Consumption > income: {int(core.consumption_above_income_count):,} "
              f"({core.consumption_above_income_pct:.1f}%)",
              transform=axis.transAxes, va="top", linespacing=1.6,
              bbox={"facecolor": WARM, "edgecolor": "none", "pad": 10})
    axis.legend(loc="lower right", frameon=False, fontsize=9)
    figure.text(0.125, 0.005,
                "Consumption = ten spending categories, excluding savings and investments. "
                "Amount period not stated by the source.", fontsize=8)
    figure.tight_layout(rect=(0, 0.035, 1, 1))
    save_figure(figure, "income_vs_consumption.png")


# Show that spending stays flat while the share spending above income falls with income.
def plot_overspend_by_income(overspend):
    deciles = overspend.loc[overspend.grouping == "income_decile"].sort_values("income_group")
    positions = np.arange(len(deciles))
    figure, axis = plt.subplots(figsize=(10, 5.8))
    bars = axis.bar(positions, deciles.above_income_pct, color=TEAL, width=0.68)
    axis.bar_label(bars, labels=[f"{value:.0f}%" for value in deciles.above_income_pct],
                   padding=3, fontsize=9)
    labels = [f"D{index + 1}\n${row.income_min / 1000:.1f}k-{row.income_max / 1000:.1f}k"
              for index, (_, row) in enumerate(deciles.iterrows())]
    axis.set_xticks(positions, labels, fontsize=8.5)
    axis.set(ylim=(0, 112), ylabel="Spending more than income (%)",
             xlabel="Income decile (lowest to highest)",
             title="Who spends more than they earn is mostly decided by income")
    axis.text(0.98, 0.95,
              f"Average consumption in every decile:\n"
              f"${deciles.consumption_mean.min():,.0f} to ${deciles.consumption_mean.max():,.0f}",
              transform=axis.transAxes, ha="right", va="top", linespacing=1.5,
              bbox={"facecolor": WARM, "edgecolor": "none", "pad": 8})
    figure.text(0.03, 0.01,
                "Each decile holds 170 records. Consumption excludes savings and investments.",
                fontsize=8)
    figure.tight_layout(rect=(0, 0.04, 1, 1))
    save_figure(figure, "overspend_by_income_decile.png")


# Show every numeric column side by side to make the even spreads visible.
def plot_column_distributions(finance):
    source = pd.read_csv(ROOT / finance["source_file"]).drop(columns=["ID"])
    figure, axes = plt.subplots(3, 5, figsize=(14, 7.6))
    for axis, column in zip(axes.flat, source.columns):
        values = source[column]
        axis.hist(values, bins=10, range=(values.min(), values.max() + 1),
                  color=TEAL, edgecolor="white")
        axis.set_title(column.replace(" (USD)", ""), fontsize=10)
        axis.set_yticks([])
        axis.tick_params(labelsize=7.5)
        axis.spines["left"].set_visible(False)
        axis.set_xlabel(f"{values.min():,.0f} to {values.max():,.0f}", fontsize=8)
    summary = finance["data_generation_check"]
    last = axes.flat[-1]
    last.axis("off")
    last.text(0, 0.5,
              f"{summary['columns_tested']} numeric columns\n"
              f"{summary['columns_rejecting_uniform_at_0_05']} reject an even spread\n(chi-square, p < 0.05)\n\n"
              f"Largest correlation between\nany two columns: {summary['max_abs_pairwise_correlation']:.2f}",
              fontsize=10, va="center", linespacing=1.5)
    figure.suptitle("Every column is spread evenly between round limits", fontsize=15,
                    fontweight="bold")
    figure.tight_layout(rect=(0, 0, 1, 0.95), h_pad=1.6)
    save_figure(figure, "column_distributions.png")


# Show both valid share definitions so the weighting choice remains visible.
def plot_category_shares(category_shares):
    shares = category_shares.loc[category_shares.segment == "all"].copy()
    shares = shares.sort_values("mean_person_consumption_share_pct")
    positions = np.arange(len(shares))
    figure, axis = plt.subplots(figsize=(9, 6.7))
    person_bars = axis.barh(positions - 0.17, shares.mean_person_consumption_share_pct,
                            height=0.3, color=NAVY, label="Mean individual share")
    aggregate_bars = axis.barh(positions + 0.17, shares.aggregate_consumption_share_pct,
                               height=0.3, color=TEAL, label="Aggregate share")
    axis.bar_label(person_bars, fmt="%.1f%%", padding=4, fontsize=8)
    axis.bar_label(aggregate_bars, fmt="%.1f%%", padding=4, fontsize=8)
    axis.set_yticks(positions, shares.category.str.replace("_", " ").str.title())
    axis.set(xlim=(0, 29), xlabel="Share of consumption (%)",
             title="Category shares depend on how records are weighted")
    axis.legend(loc="lower right", frameon=False)
    figure.text(0.03, 0.01,
                "Mean individual share: mean(category / person consumption). "
                "Aggregate share: sum(category) / sum(consumption).\n"
                f"n = {int(shares.n.iloc[0]):,}. Savings/investments excluded. "
                "Amount period not stated by the source.",
                fontsize=8, linespacing=1.5)
    figure.tight_layout(rect=(0, 0.07, 1, 1))
    save_figure(figure, "consumption_category_shares.png")


# Compare all four planned shopping outcomes in the separate synthetic sample.
def plot_shopping_preferences(preferences, tests, groups):
    figure, axes = plt.subplots(2, 2, figsize=(12, 8.2))
    names = {"payment": "Preferred payment", "shipping": "Shipping type",
             "frequency": "Purchase frequency", "category": "Purchase category"}
    group_sizes = dict(zip(groups.age_group, groups.n))
    for axis, preference in zip(axes.flat, names):
        values = preferences.loc[preferences.preference == preference]
        wide = values.pivot(index="preference_value", columns="age_group", values="percent")
        wide = wide.reindex(columns=["18-27", "28-70"]).sort_index()
        positions = np.arange(len(wide))
        for offset, age_group, color in [(-0.18, "18-27", TEAL), (0.18, "28-70", NAVY)]:
            axis.barh(positions + offset, wide[age_group], height=0.32,
                       color=color, label=f"Age {age_group} (n={int(group_sizes[age_group]):,})")
        result = tests.loc[tests.preference == preference].iloc[0]
        axis.set_yticks(positions, wide.index)
        axis.invert_yaxis()
        axis.set_xlim(0, max(30, wide.max().max() * 1.18))
        axis.set_xlabel("Within-age-group share (%)")
        axis.set_title(f"{names[preference]}\nHolm p = {result.p_holm:.3f}; "
                       f"Cramer's V = {result.cramers_v:.3f}", fontsize=11)
        axis.tick_params(labelsize=9)
    handles, labels = axes[0, 0].get_legend_handles_labels()
    figure.legend(handles, labels, loc="upper center", bbox_to_anchor=(0.5, 0.94),
                  ncol=2, frameon=False)
    figure.suptitle("Synthetic shopping records: age comparisons illustrate a method", fontsize=15,
                     fontweight="bold", y=0.99)
    figure.text(0.03, 0.015,
                "Four chi-square tests, Holm adjustment, alpha = 0.05. "
                "Frequency synonyms are combined as documented.\n"
                "Age groups are not verified generations. These synthetic records provide no "
                "evidence about real Gen Z customers; no financial-data join.", fontsize=8,
                linespacing=1.5)
    figure.tight_layout(rect=(0, 0.07, 1, 0.89), h_pad=2, w_pad=2.4)
    save_figure(figure, "shopping_preferences.png")


# Require the completed analysis outputs instead of filling missing inputs.
def main():
    required = ["finance_results.json", "finance_core_metrics.csv", "finance_overspend_by_income.csv",
                "finance_category_shares.csv", "shopping_preferences.csv", "shopping_tests.csv",
                "shopping_age_group_summary.csv"]
    missing = [name for name in required if not (TABLES / name).is_file()]
    if missing:
        raise FileNotFoundError("Run the finance and shopping analyses first: " + ", ".join(missing))
    FIGURES.mkdir(parents=True, exist_ok=True)
    finance = json.loads((TABLES / "finance_results.json").read_text())
    core = pd.read_csv(TABLES / "finance_core_metrics.csv").iloc[0]
    plot_income_consumption(core, finance)
    plot_overspend_by_income(pd.read_csv(TABLES / "finance_overspend_by_income.csv"))
    plot_column_distributions(finance)
    plot_category_shares(pd.read_csv(TABLES / "finance_category_shares.csv"))
    plot_shopping_preferences(pd.read_csv(TABLES / "shopping_preferences.csv"),
                               pd.read_csv(TABLES / "shopping_tests.csv"),
                               pd.read_csv(TABLES / "shopping_age_group_summary.csv"))
    print("Created five figures from the verified local outputs.")


# Run the script only when called directly.
if __name__ == "__main__":
    main()
