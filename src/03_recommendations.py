"""Turn the verified findings into three plain recommendations for a real-data version."""

# Read the verified finance and shopping tables that each recommendation relies on.
from pathlib import Path
import json

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
TABLES = ROOT / "outputs/tables"
core = pd.read_csv(TABLES / "finance_core_metrics.csv").iloc[0]
overspend = pd.read_csv(TABLES / "finance_overspend_by_income.csv")
tests = pd.read_csv(TABLES / "shopping_tests.csv")
generation = json.loads((TABLES / "finance_results.json").read_text())["data_generation_check"]

# Pull the few numbers the recommendations quote.
deciles = overspend.loc[overspend.grouping == "income_decile"]
low_spend = deciles.consumption_mean.min()
high_spend = deciles.consumption_mean.max()
significant = int((tests.p_holm < 0.05).sum())
max_v = tests.cramers_v.max()
max_r = generation["max_abs_pairwise_correlation"]

# Keep each recommendation tied to one piece of evidence from this repository.
rows = [
    {
        "number": 1,
        "evidence_en": (
            f"Income and consumption are unrelated in this file (r = {core.income_consumption_pearson_r:.2f}); "
            f"average consumption stays between ${low_spend:,.0f} and ${high_spend:,.0f} in every income decile."
        ),
        "evidence_zh": (
            f"本数据中收入与消费几乎无关（r = {core.income_consumption_pearson_r:.2f}），"
            f"每个收入十分位的平均消费都在 {low_spend:,.0f} 到 {high_spend:,.0f} 美元之间。"
        ),
        "action_en": "Segment real customers on what they actually buy (category mix, repeat purchases, response to past promotions), not on income or age alone.",
        "action_zh": "用真实客户的实际购买行为分群（品类结构、复购、对过往促销的反应），而不是只按收入或年龄。",
    },
    {
        "number": 2,
        "evidence_en": (
            f"In the synthetic shopping data, {significant} of 4 comparisons (payment, shipping, frequency, category) "
            f"differ between ages 18-27 and 28-70 after correction (Cramer's V at most {max_v:.2f})."
        ),
        "evidence_zh": (
            f"在合成购物数据中，支付、配送、购买频率、品类四项比较经校正后，18-27 岁和 28-70 岁之间"
            f"有 {significant} 项存在差异（Cramer's V 最大 {max_v:.2f}）。"
        ),
        "action_en": "Start with one shared offer, then A/B test single changes (price, delivery fee, promotion timing) on small groups before rolling them out.",
        "action_zh": "先用一个统一方案，再在小范围内一次只测试一个变化（价格、运费、促销时间），有效再推广。",
    },
    {
        "number": 3,
        "evidence_en": (
            f"A quick distribution check showed every numeric column spread evenly between round limits, "
            f"with no pair of columns correlated above {max_r:.2f}."
        ),
        "evidence_zh": f"简单的分布检查显示，每个数值列都在整数上下限之间均匀分布，任意两列的相关系数都不超过 {max_r:.2f}。",
        "action_en": "Check where a dataset comes from and how it is distributed before building recommendations on it.",
        "action_zh": "在基于数据提出建议之前，先确认数据来源，并检查它的分布是否合理。",
    },
]

# Export the shared wording used by the README and both one-page summaries.
pd.DataFrame(rows).to_csv(TABLES / "marketing_actions.csv", index=False)
print("Saved three evidence-linked recommendations.")
