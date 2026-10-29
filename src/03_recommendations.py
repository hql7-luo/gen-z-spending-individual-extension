"""Connect four descriptive financial profiles to testable marketing actions."""

# Read the actual financial profiles produced by the SQL analysis.
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
TABLES = ROOT / "outputs/tables"
profiles = pd.read_csv(TABLES / "finance_segments.csv").set_index("segment")

# Keep one plain, explicit hypothesis for each of the four designed groups.
actions = [
    ("A", "lower_income_above_income",
     "Test a small, one-time starter bundle with its full price visible before checkout.",
     "测试小份、一次性入门组合，在结账前显示完整价格。"),
    ("B", "lower_income_not_above_income",
     "Test an optional low-entry education or fitness trial without automatic renewal.",
     "测试可选的低门槛教育或健身体验，不自动续费。"),
    ("C", "higher_income_above_income",
     "Test a fixed-total-price education and fitness bundle, without installment or credit messaging.",
     "测试总价固定的教育和健身组合，不使用分期或信贷营销。"),
    ("D", "higher_income_not_above_income",
     "Test an optional experience upgrade alongside a clearly priced standard offer.",
     "在明码标价的标准方案旁，测试可选的体验升级。"),
]

# Attach observed amounts and shares, rather than inventing campaign outcomes.
rows = []
for label, segment, action_en, action_zh in actions:
    p = profiles.loc[segment]
    evidence_en = (
        f"n={int(p['n'])}; mean income USD {p['income_mean']:.0f}; "
        f"mean consumption USD {p['consumption_mean']:.0f}; "
        f"education + fitness {p['mean_person_self_investment_consumption_share_pct']:.1f}% "
        f"of individual consumption; travel + entertainment mean USD {p['enjoyment_mean']:.0f}."
    )
    evidence_zh = (
        f"{int(p['n'])}条记录；平均收入{p['income_mean']:.0f}美元；"
        f"平均消费{p['consumption_mean']:.0f}美元；教育与健身平均个人消费占比"
        f"{p['mean_person_self_investment_consumption_share_pct']:.1f}%；"
        f"旅行与娱乐平均金额{p['enjoyment_mean']:.0f}美元。"
    )
    rows.append({
        "group": label, "segment": segment, "n": int(p["n"]),
        "sample_pct": p["sample_pct"], "evidence_en": evidence_en,
        "evidence_zh": evidence_zh, "action_en": action_en, "action_zh": action_zh,
        "status_en": "Exploratory hypothesis; effectiveness and willingness to pay were not measured.",
        "status_zh": "探索性假设；尚未测量营销效果或支付意愿。",
        "validation_en": "In a small opt-in test, compare take-up and cancellations with a standard offer.",
        "validation_zh": "以自愿参加的小规模测试，对照标准方案比较选择率与取消率。",
    })

# Export the shared wording used by the bilingual summaries.
pd.DataFrame(rows).to_csv(TABLES / "marketing_actions.csv", index=False, float_format="%.15g")
print("Saved four evidence-linked marketing hypotheses; amount periods remain unspecified.")
