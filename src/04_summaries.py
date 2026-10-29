"""Export matching English and Chinese one-page summaries from analysis tables."""

# Import document tools and keep every numerical statement tied to a saved table.
from html import escape
import json
from pathlib import Path

import pandas as pd
from reportlab.lib.colors import HexColor, white
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph


# Define a shared visual style and the same rule order used by the figures.
ROOT = Path(__file__).resolve().parents[1]
TABLES = ROOT / "outputs/tables"
OUTPUT = ROOT / "outputs"
SEGMENTS = [
    "lower_income_above_income", "lower_income_not_above_income",
    "higher_income_above_income", "higher_income_not_above_income",
]
FINANCE_URL = "https://www.kaggle.com/datasets/manandkumar/gen-z-money-spending-dataset"
SHOPPING_URL = "https://www.kaggle.com/datasets/iamsouravbanerjee/customer-shopping-trends-dataset"
NAVY = HexColor("#17324D")
TEAL = HexColor("#217F80")
GRAY = HexColor("#59666F")
WARM = HexColor("#F6F4EF")
RULE_NAMES = {
    "en": ["Lower income; consumption > income", "Lower income; consumption <= income",
           "Higher income; consumption > income", "Higher income; consumption <= income"],
    "zh": ["较低收入；消费高于收入", "较低收入；消费不高于收入",
           "较高收入；消费高于收入", "较高收入；消费不高于收入"],
}
CHINESE_FONT = "STSong-Light"
TESTS = {"en": [], "zh": []}


# Format all displayed values from the actual calculation outputs.
def load_results():
    required = ["finance_core_metrics.csv", "finance_segments.csv", "finance_denominator_audit.csv", "marketing_actions.csv",
                "shopping_tests.csv", "shopping_age_group_summary.csv", "shopping_results.json"]
    missing = [name for name in required if not (TABLES / name).is_file()]
    if missing:
        raise FileNotFoundError("Run both analyses before exporting summaries: " + ", ".join(missing))
    core = pd.read_csv(TABLES / "finance_core_metrics.csv").iloc[0]
    segments = pd.read_csv(TABLES / "finance_segments.csv").set_index("segment").loc[SEGMENTS]
    audit = pd.read_csv(TABLES / "finance_denominator_audit.csv")
    tests = pd.read_csv(TABLES / "shopping_tests.csv")
    groups = pd.read_csv(TABLES / "shopping_age_group_summary.csv").set_index("age_group")
    shopping = json.loads((TABLES / "shopping_results.json").read_text())
    shares = audit.loc[audit.denominator == "consumption"].set_index("allocation_group")
    return core, segments, shares, tests, groups, shopping


# Build concise bilingual text without interpreting descriptive groups as preferences.
def summary_text(language, core, shares, tests, groups, shopping):
    significant = int((tests.p_holm < 0.05).sum())
    young_n = int(groups.loc["18-27", "n"])
    older_n = int(groups.loc["28-70", "n"])
    self_share = shares.loc["self_investment", "mean_person_share_pct"]
    enjoyment_share = shares.loc["enjoyment", "mean_person_share_pct"]
    if language == "en":
        return {
            "title": "Gen Z spending: profiles to test",
            "subtitle": "Independent extension of a UW IS 445 course group project",
            "metrics": [
                (f"{int(core.n_included):,}", f"financial records | ages {int(core.age_min)}-{int(core.age_max)}"),
                (f"{core.income_consumption_pearson_r:.4f}", "Pearson r: income vs consumption"),
                (f"{core.consumption_above_income_pct:.2f}%", "consumption > income"),
            ],
            "definition": (
                "Consumption sums ten categories and excludes savings/investments. "
                f"Mean individual consumption shares: education + fitness {self_share:.2f}%; "
                f"travel + entertainment {enjoyment_share:.2f}%. These are analyst-defined groupings."
            ),
            "segment_heading": "Four designed financial groups | one marketing test each",
            "rule": (
                f"Lower income < sample median ${core.income_median:,.0f}; higher income >= median. "
                "Crossed with consumption > income versus <= income. No natural clusters are claimed."
            ),
            "shopping_heading": "Separate shopping check | synthetic learning data",
            "shopping": (
                f"Age 18-27: n={young_n:,}; age 28-70: n={older_n:,}. Payment, shipping, "
                f"frequency and category: {significant}/4 comparisons have Holm-adjusted p < 0.05 "
                f"(adjusted p {tests.p_holm.min():.3f}-{tests.p_holm.max():.3f}; "
                f"Cramer's V {tests.cramers_v.min():.3f}-{tests.cramers_v.max():.3f}). "
                "This is a method demonstration, not evidence for real-customer targeting."
            ),
            "limits_heading": "Interpretation limits",
            "limits": (
                "Financial sampling, collection period and real-versus-synthetic origin are unknown. "
                "USD amounts have no documented time unit. Shopping data are synthetic; the two samples "
                "are not joined. Correlation is not causation. Test suggestions are hypotheses, with no "
                "measured effectiveness or established preference differences."
            ),
            "sources": "Sources: Financial v1 (2025-01-31, CC0) | Shopping v2 (synthetic)",
            "credit": (
                "Course context: March-June 2025 group project. hql7-luo's original role: SQL/Excel/Python "
                "data analysis and visualization. This individual extension re-runs the analysis with "
                "explicit definitions, rule groups and separate age comparisons."
            ),
        }
    return {
        "title": "Gen Z 消费：可检验的财务画像",
        "subtitle": "UW IS 445 课程小组项目的个人独立扩展",
        "metrics": [
            (f"{int(core.n_included):,}", f"条财务记录 | 年龄 {int(core.age_min)}-{int(core.age_max)} 岁"),
            (f"{core.income_consumption_pearson_r:.4f}", "收入与消费的 Pearson r"),
            (f"{core.consumption_above_income_pct:.2f}%", "消费高于收入的记录占比"),
        ],
        "definition": (
            "消费为十个支出类别之和，不含储蓄与投资。以每人消费为分母，再对个人占比取平均："
            f"教育 + 健身占 {self_share:.2f}%，旅行 + 娱乐占 {enjoyment_share:.2f}%。"
            "这两类为分析者设定的归类，不代表态度或投资回报。"
        ),
        "segment_heading": "四个规则分组 | 每组一个营销测试建议",
        "rule": (
            f"较低收入：低于样本收入中位数 ${core.income_median:,.0f}；较高收入：不低于中位数。"
            "再按消费是否高于收入交叉分组。这是预设规则，不是发现的自然群体。"
        ),
        "shopping_heading": "独立购物分析 | 仅用于学习的合成数据",
        "shopping": (
            f"18-27 岁 n={young_n:,}，28-70 岁 n={older_n:,}。支付、配送、购买频率、商品类别的"
            f"四项卡方检验中，{significant}/4 项通过 Holm 校正后的 p < 0.05 "
            f"（校正 p 为 {tests.p_holm.min():.3f}-{tests.p_holm.max():.3f}；"
            f"Cramer's V 为 {tests.cramers_v.min():.3f}-{tests.cramers_v.max():.3f}）。"
            "这只是方法示范，不能据此对真实消费者定向营销。"
        ),
        "limits_heading": "解释边界",
        "limits": (
            "财务数据的抽样方法、采集时期及真实或合成来源均不明，美元数值没有已知的时间单位。"
            "购物数据明确为合成数据；两个样本未连接。相关不代表因果。"
            "营销建议仅为待验证的假设，未测量效果，也未证明分组间偏好不同。"
        ),
        "sources": "来源：财务 v1（2025-01-31，CC0）| 购物 v2（合成数据）",
        "credit": (
            "课程背景：2025 年 3-6 月小组项目。hql7-luo 原负责 SQL / Excel / Python 数据分析与可视化。"
            "本次为课程结束后的个人扩展，重新计算指标，明确分母、规则分组与独立年龄比较。"
        ),
    }


# Write matching, readable Markdown versions with explicit machine-table rule labels.
def write_markdown(language, text, core, segments):
    lines = [f"# {text['title']}", "", text["subtitle"], ""]
    for value, label in text["metrics"]:
        lines.append(f"- **{value}**: {label}")
    lines += ["", text["definition"], "", f"## {text['segment_heading']}", "", text["rule"], ""]
    if language == "en":
        lines += ["| Group and rule | n (%) | Mean income / consumption (USD, period unknown) | Test hypothesis |",
                  "| --- | ---: | ---: | --- |"]
    else:
        lines += ["| 分组与规则 | n（占比）| 平均收入 / 消费（美元，时期未知）| 测试假设 |",
                  "| --- | ---: | ---: | --- |"]
    for index, (segment, row) in enumerate(segments.iterrows()):
        lines.append(
            f"| {chr(65 + index)}: {RULE_NAMES[language][index]}<br>`{segment}` "
            f"| {int(row.n):,} ({row.sample_pct:.2f}%) "
            f"| ${row.income_mean:,.0f} / ${row.consumption_mean:,.0f} "
            f"| {TESTS[language][index]} |"
        )
    lines += ["", f"## {text['shopping_heading']}", "", text["shopping"], "",
              f"## {text['limits_heading']}", "", text["limits"], "", text["sources"], "",
              f"- [Gen Z Money Spending Dataset]({FINANCE_URL})",
              f"- [Customer Shopping Trends Dataset]({SHOPPING_URL})", "", text["credit"], ""]
    (OUTPUT / f"summary_{language}.md").write_text("\n".join(lines), encoding="utf-8")


# Draw wrapped text and return its bottom edge for simple layout checks.
def paragraph(document, content, x, top, width, font, size=9, color=GRAY, leading=None):
    style = ParagraphStyle("body", fontName=font, fontSize=size,
                           leading=leading or size * 1.32, textColor=color,
                           wordWrap="CJK" if font not in ["Helvetica", "Helvetica-Bold"] else None)
    block = Paragraph(content, style)
    block_width, block_height = block.wrap(width, 1000)
    block.drawOn(document, x, top - block_height)
    return top - block_height


# Create a single-page brief with readable cards, group rows, and source links.
def write_pdf(language, text, core, segments):
    filename = OUTPUT / f"summary_{language}.pdf"
    document = canvas.Canvas(str(filename), pagesize=(612, 792), invariant=1)
    document.setTitle(text["title"])
    document.setAuthor("hql7-luo")
    font = "Helvetica" if language == "en" else CHINESE_FONT
    bold = "Helvetica-Bold" if language == "en" else font
    document.setFillColor(NAVY)
    document.rect(0, 687, 612, 105, fill=1, stroke=0)
    paragraph(document, "INDIVIDUAL EXTENSION  /  UW IS 445", 32, 769, 548,
              bold, 8.2, white)
    paragraph(document, escape(text["title"]), 32, 746, 548, bold, 23, white, 27)
    paragraph(document, escape(text["subtitle"]), 32, 710, 548, font, 10, white)

    # Use large numbers and plain labels for the three central results.
    card_width = (548 - 20) / 3
    for index, (value, label) in enumerate(text["metrics"]):
        x = 32 + index * (card_width + 10)
        document.setFillColor(WARM)
        document.roundRect(x, 613, card_width, 60, 5, fill=1, stroke=0)
        paragraph(document, value, x + 11, 664, card_width - 22, bold, 23, TEAL)
        paragraph(document, escape(label), x + 11, 634, card_width - 22, font, 8.1, NAVY)
    bottom = paragraph(document, escape(text["definition"]), 32, 600, 548,
                       font, 9.0, GRAY, 11.7)
    if bottom < 560:
        raise ValueError("Definition text exceeds its page allocation.")

    # State the segmentation rules before presenting the four candidate tests.
    paragraph(document, escape(text["segment_heading"]), 32, 553, 548, bold, 11.1, NAVY)
    bottom = paragraph(document, escape(text["rule"]), 32, 535, 548, font, 8.6, GRAY, 11.3)
    if bottom < 508:
        raise ValueError("Segment rules exceed their page allocation.")
    row_top = 500
    for index, (_, row) in enumerate(segments.iterrows()):
        document.setFillColor(WARM if index % 2 == 0 else white)
        document.rect(32, row_top - 64, 548, 64, fill=1, stroke=0)
        document.setFillColor(TEAL)
        document.roundRect(40, row_top - 26, 20, 20, 4, fill=1, stroke=0)
        paragraph(document, chr(65 + index), 46, row_top - 10, 15,
                  bold, 10, white)
        heading = f"{RULE_NAMES[language][index]} | n={int(row.n):,} ({row.sample_pct:.2f}%)"
        paragraph(document, escape(heading), 69, row_top - 7, 501, bold, 9.2, NAVY, 12)
        amount_label = ("Mean income" if language == "en" else "平均收入")
        consumption_label = ("consumption" if language == "en" else "平均消费")
        amounts = (f"{amount_label} ${row.income_mean:,.0f}; "
                   f"{consumption_label} ${row.consumption_mean:,.0f} "
                   + ("(USD; period unknown)." if language == "en" else "（美元；时期未知）。"))
        paragraph(document, escape(amounts), 69, row_top - 22, 501, font, 8.6, GRAY, 11)
        test_label = ""
        bottom = paragraph(document, escape(test_label + TESTS[language][index]),
                           69, row_top - 36, 501, font, 8.8, TEAL, 11.2)
        if bottom < row_top - 61:
            raise ValueError("A marketing test exceeds its row allocation.")
        row_top -= 64

    # Keep the synthetic-data demonstration separate from financial segmentation.
    paragraph(document, escape(text["shopping_heading"]), 32, 232, 548, bold, 10.7, NAVY)
    bottom = paragraph(document, escape(text["shopping"]), 32, 215, 548, font, 8.5, GRAY, 11.1)
    if bottom < 167:
        raise ValueError("Shopping text exceeds its page allocation.")
    paragraph(document, escape(text["limits_heading"]), 32, 158, 548, bold, 10.1, NAVY)
    bottom = paragraph(document, escape(text["limits"]), 32, 142, 548, font, 8.2, GRAY, 10.6)
    if bottom < 96:
        raise ValueError("Limitations text exceeds its page allocation.")

    # Add two clickable source labels and preserve the course-versus-extension credit.
    paragraph(document, escape(text["sources"]), 32, 88, 548, font, 7.8, GRAY, 10)
    links = (f'<link href="{FINANCE_URL}" color="#217F80">Financial dataset</link>'
             '  |  '
             f'<link href="{SHOPPING_URL}" color="#217F80">Synthetic shopping dataset</link>')
    paragraph(document, links, 32, 75, 548, "Helvetica", 7.8, TEAL, 10)
    document.setStrokeColor(HexColor("#D8DDD9"))
    document.line(32, 58, 580, 58)
    bottom = paragraph(document, escape(text["credit"]), 32, 50, 548,
                       font, 7.3, GRAY, 9.2)
    if bottom < 18:
        raise ValueError("Attribution text exceeds the bottom margin.")
    document.showPage()
    document.save()


# Register a portable built-in Chinese CID font and generate matching exports.
def main():
    global CHINESE_FONT
    core, segments, shares, tests, groups, shopping = load_results()
    # Use the shared evidence-linked actions so both summaries agree with the README.
    actions = pd.read_csv(TABLES / "marketing_actions.csv").set_index("segment").loc[SEGMENTS]
    for language in ["en", "zh"]:
        TESTS[language] = actions[f"action_{language}"].tolist()
    pdfmetrics.registerFont(UnicodeCIDFont("STSong-Light"))
    available_font = Path("/System/Library/Fonts/Supplemental/Arial Unicode.ttf")
    if available_font.is_file():
        pdfmetrics.registerFont(TTFont("ChineseUnicode", str(available_font)))
        CHINESE_FONT = "ChineseUnicode"
    OUTPUT.mkdir(parents=True, exist_ok=True)
    for language in ["en", "zh"]:
        text = summary_text(language, core, shares, tests, groups, shopping)
        write_markdown(language, text, core, segments)
        write_pdf(language, text, core, segments)
    print("Created English and Chinese Markdown summaries and one-page PDFs.")


# Run the export only when called directly.
if __name__ == "__main__":
    main()
