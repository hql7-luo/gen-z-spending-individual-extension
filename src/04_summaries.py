"""Export matching English and Chinese one-page summaries from the analysis tables."""

# Import document tools and keep every number tied to a saved table.
from html import escape
import json
import os
from pathlib import Path

import pandas as pd
from reportlab.lib.colors import HexColor, white
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph


# Shared paths, links and colors.
ROOT = Path(__file__).resolve().parents[1]
TABLES = ROOT / "outputs/tables"
OUTPUT = ROOT / "outputs"
FINANCE_URL = "https://www.kaggle.com/datasets/manandkumar/gen-z-money-spending-dataset"
SHOPPING_URL = "https://www.kaggle.com/datasets/iamsouravbanerjee/customer-shopping-trends-dataset"
NAVY = HexColor("#17324D")
TEAL = HexColor("#217F80")
GRAY = HexColor("#59666F")
LIGHT = HexColor("#D8DDD9")
WARM = HexColor("#F6F4EF")
FONTS = {"en": ("Helvetica", "Helvetica-Bold"), "zh": ("STSong-Light", "STSong-Light")}


# Read every table the summaries quote.
def load_results():
    required = ["finance_core_metrics.csv", "finance_overspend_by_income.csv", "finance_results.json",
                "marketing_actions.csv", "shopping_tests.csv", "shopping_age_group_summary.csv"]
    missing = [name for name in required if not (TABLES / name).is_file()]
    if missing:
        raise FileNotFoundError("Run the analyses before exporting summaries: " + ", ".join(missing))
    return {
        "core": pd.read_csv(TABLES / "finance_core_metrics.csv").iloc[0],
        "overspend": pd.read_csv(TABLES / "finance_overspend_by_income.csv"),
        "generation": json.loads((TABLES / "finance_results.json").read_text())["data_generation_check"],
        "actions": pd.read_csv(TABLES / "marketing_actions.csv").sort_values("number"),
        "tests": pd.read_csv(TABLES / "shopping_tests.csv"),
        "groups": pd.read_csv(TABLES / "shopping_age_group_summary.csv").set_index("age_group"),
    }


# Build the wording for one language, with numbers rounded for reading.
def summary_text(language, data):
    core, overspend, generation, tests = data["core"], data["overspend"], data["generation"], data["tests"]
    halves = overspend.loc[overspend.grouping == "income_half"].set_index("income_group")
    below = halves.loc["below_median", "above_income_pct"]
    above = halves.loc["at_or_above_median", "above_income_pct"]
    typical_spend = round(core.consumption_mean, -2)
    significant = int((tests.p_holm < 0.05).sum())
    max_r = generation["max_abs_pairwise_correlation"]
    columns = generation["columns_tested"]
    r = core.income_consumption_pearson_r
    if language == "en":
        return {
            "kicker": "INDIVIDUAL EXTENSION  /  UW IS 445",
            "title": "Gen Z spending: re-checking a course project",
            "subtitle": "Individual extension of a UW IS 445 group project (2025)",
            "metrics": [
                (f"{int(core.n_included):,}", f"financial records, ages {int(core.age_min)}-{int(core.age_max)}"),
                (f"{r:.2f}", "correlation: income vs consumption"),
                (f"{core.consumption_above_income_pct:.1f}%", "spend more than they earn"),
            ],
            "note": "Both numbers match the original course presentation. Rebuilt in SQLite and checked independently in Python.",
            "findings_heading": "What the re-check found",
            "findings": [
                ("The financial data looks randomly generated",
                 f"All {columns} numeric columns are spread evenly between round limits (income: "
                 f"${core.income_min:,.0f} to ${core.income_max:,.0f}), and no two columns correlate above "
                 f"{max_r:.2f}. The near-zero correlation reflects how the file was built, not how Gen Z spends."),
                ("Spending above income is mostly an income effect",
                 f"Average consumption is about ${typical_spend:,.0f} at every income level, so {below:.0f}% of "
                 f"below-median earners spend more than they earn, versus {above:.0f}% of everyone else."),
                ("Age groups shop the same way (synthetic data)",
                 f"In a separate synthetic shopping dataset, {significant} of 4 comparisons (payment, shipping, "
                 "frequency, category) differ between ages 18-27 and 28-70 after Holm correction."),
            ],
            "chart_title": "Spending more than income, by income decile",
            "chart_caption": "Lowest to highest income",
            "recs_heading": "What I would do with real customer data",
            "limits": ("Limits: the two datasets are separate and never joined; amounts are USD with no stated "
                       "period; results describe these files, not real Gen Z consumers."),
            "sources": "Sources: Financial v1 (2025-01-31, CC0)  |  Shopping v2 (synthetic)",
            "links": ("Financial dataset", "Synthetic shopping dataset"),
            "credit": ("Course context: UW IS 445 group project, March-June 2025. My role: data analysis and "
                       "visualization with SQL, Excel and Python. I rebuilt this extension on my own in "
                       "October 2026, after the original course files were lost."),
        }
    return {
        "kicker": "INDIVIDUAL EXTENSION  /  UW IS 445",
        "title": "Gen Z 消费：课程项目的重新核对",
        "subtitle": "UW IS 445 课程小组项目（2025）的个人扩展",
        "metrics": [
            (f"{int(core.n_included):,}", f"条财务记录，{int(core.age_min)}-{int(core.age_max)} 岁"),
            (f"{r:.2f}", "收入与消费的相关系数"),
            (f"{core.consumption_above_income_pct:.1f}%", "消费高于收入"),
        ],
        "note": "两个数字都与课程原报告一致。用 SQLite 重建，并用 Python 独立核对。",
        "findings_heading": "重新核对的发现",
        "findings": [
            ("财务数据看起来是随机生成的",
             f"{columns} 个数值列都在整数上下限之间均匀分布，例如收入从 {core.income_min:,.0f} 到 "
             f"{core.income_max:,.0f} 美元；任意两列的相关系数都不超过 {max_r:.2f}。相关系数接近 0，"
             "反映的是数据的生成方式，而不是 Gen Z 的消费规律。"),
            ("消费高于收入，主要由收入高低决定",
             f"各收入水平的平均消费都在 {typical_spend:,.0f} 美元左右，所以收入低于中位数的人中有 "
             f"{below:.0f}% 消费高于收入，而收入不低于中位数的人中只有 {above:.0f}%。"),
            ("不同年龄组的购物偏好基本相同（合成数据）",
             f"在另一份合成购物数据中，18-27 岁与 28-70 岁在支付、配送、购买频率和品类四项比较上，"
             f"经 Holm 校正后有 {significant} 项存在差异。"),
        ],
        "chart_title": "各收入十分位中消费高于收入的比例",
        "chart_caption": "收入从低到高",
        "recs_heading": "如果有真实客户数据，我会这样做",
        "limits": "说明：两份数据相互独立，未做合并；金额单位为美元，未注明周期；结论只描述这两份数据，不代表真实的 Gen Z 消费者。",
        "sources": "来源：财务数据 v1（2025-01-31，CC0）| 购物数据 v2（合成数据）",
        "links": ("Financial dataset", "Synthetic shopping dataset"),
        "credit": ("课程背景：UW IS 445 小组项目，2025 年 3-6 月。我负责用 SQL、Excel 和 Python 做数据分析与可视化。"
                   "原始课程文件遗失后，我在 2026 年 10 月独立重建了这个扩展项目。"),
    }


# Write a Markdown version with the same content.
def write_markdown(language, text, data):
    lines = [f"# {text['title']}", "", text["subtitle"], ""]
    for value, label in text["metrics"]:
        lines.append(f"- **{value}** {label}")
    lines += ["", text["note"], "", f"## {text['findings_heading']}", ""]
    for number, (title, body) in enumerate(text["findings"], start=1):
        lines += [f"{number}. **{title}.** {body}", ""]
    deciles = data["overspend"].loc[data["overspend"].grouping == "income_decile"].sort_values("income_group")
    shares = ", ".join(f"D{index + 1} {value:.0f}%" for index, value in enumerate(deciles.above_income_pct))
    lines += [f"{text['chart_title']}: {shares}", "", f"## {text['recs_heading']}", ""]
    for _, row in data["actions"].iterrows():
        lines += [f"{int(row.number)}. {row[f'action_{language}']} {row[f'evidence_{language}']}", ""]
    lines += [text["limits"], "", text["sources"], "",
              f"- [{text['links'][0]}]({FINANCE_URL})",
              f"- [{text['links'][1]}]({SHOPPING_URL})", "", text["credit"], ""]
    (OUTPUT / f"summary_{language}.md").write_text("\n".join(lines), encoding="utf-8")


# Draw wrapped text and return its bottom edge so the layout can stack blocks.
def paragraph(document, content, x, top, width, font, size=9, color=GRAY, leading=None):
    style = ParagraphStyle("body", fontName=font, fontSize=size, leading=leading or size * 1.35,
                           textColor=color, wordWrap=None if font.startswith("Helvetica") else "CJK")
    block = Paragraph(content, style)
    _, height = block.wrap(width, 1000)
    block.drawOn(document, x, top - height)
    return top - height


# Draw a small bar chart of the overspending share in each income decile.
def draw_decile_chart(document, text, deciles, x, top, width, height, font, bold):
    document.setFillColor(WARM)
    document.roundRect(x, top - height, width, height, 5, fill=1, stroke=0)
    paragraph(document, escape(text["chart_title"]), x + 10, top - 9, width - 20, bold, 8.6, NAVY, 11)
    base = top - height + 30
    plot_height = height - 70
    slot = (width - 20) / len(deciles)
    document.setStrokeColor(LIGHT)
    document.line(x + 10, base, x + width - 10, base)
    for index, value in enumerate(deciles.above_income_pct):
        bar_x = x + 10 + index * slot + slot * 0.18
        bar_height = plot_height * value / 100
        document.setFillColor(TEAL)
        if bar_height > 0:
            document.rect(bar_x, base, slot * 0.64, bar_height, fill=1, stroke=0)
        document.setFillColor(NAVY)
        document.setFont("Helvetica", 6.6)
        document.drawCentredString(bar_x + slot * 0.32, base + bar_height + 3, f"{value:.0f}%")
        document.setFillColor(GRAY)
        document.drawCentredString(bar_x + slot * 0.32, base - 9, f"D{index + 1}")
    paragraph(document, escape(text["chart_caption"]), x + 10, base - 13, width - 20, font, 7.4, GRAY, 9)


# Lay out the one-page brief and check that each block fits its space.
def write_pdf(language, text, data):
    font, bold = FONTS[language]
    document = canvas.Canvas(str(OUTPUT / f"summary_{language}.pdf"), pagesize=(612, 792), invariant=1)
    document.setTitle(text["title"])
    document.setAuthor("Haoqi Luo")

    # Header band.
    document.setFillColor(NAVY)
    document.rect(0, 687, 612, 105, fill=1, stroke=0)
    paragraph(document, text["kicker"], 32, 769, 548, "Helvetica-Bold", 8.2, white)
    paragraph(document, escape(text["title"]), 32, 746, 548, bold, 22, white, 27)
    paragraph(document, escape(text["subtitle"]), 32, 709, 548, font, 10, white)

    # Three headline numbers.
    card_width = (548 - 20) / 3
    for index, (value, label) in enumerate(text["metrics"]):
        x = 32 + index * (card_width + 10)
        document.setFillColor(WARM)
        document.roundRect(x, 613, card_width, 60, 5, fill=1, stroke=0)
        paragraph(document, value, x + 11, 664, card_width - 22, "Helvetica-Bold", 23, TEAL)
        paragraph(document, escape(label), x + 11, 634, card_width - 22, font, 8.4, NAVY)
    paragraph(document, escape(text["note"]), 32, 602, 548, font, 8.6, GRAY, 11)

    # Findings on the left, decile chart on the right.
    paragraph(document, escape(text["findings_heading"]), 32, 574, 548, bold, 12, NAVY)
    top = 552
    for number, (title, body) in enumerate(text["findings"], start=1):
        document.setFillColor(TEAL)
        document.circle(40, top - 6, 7, fill=1, stroke=0)
        document.setFillColor(white)
        document.setFont("Helvetica-Bold", 8.5)
        document.drawCentredString(40, top - 9, str(number))
        bottom = paragraph(document, escape(title), 54, top, 296, bold, 10, NAVY, 13)
        top = paragraph(document, escape(body), 54, bottom - 2, 296, font, 9, GRAY, 12.4) - 14
    deciles = data["overspend"].loc[data["overspend"].grouping == "income_decile"].sort_values("income_group")
    chart_bottom = 556 - 214
    draw_decile_chart(document, text, deciles, 364, 556, 216, 214, font, bold)
    if top < 320:
        raise ValueError("Findings exceed their page allocation.")

    # Recommendations across the full width.
    top = min(top, chart_bottom) - 24
    paragraph(document, escape(text["recs_heading"]), 32, top, 548, bold, 12, NAVY)
    top -= 24
    for _, row in data["actions"].iterrows():
        document.setFillColor(TEAL)
        document.rect(34, top - 10, 3, 10, fill=1, stroke=0)
        bottom = paragraph(document, escape(row[f"action_{language}"]), 46, top, 534, bold, 9.6, NAVY, 12.6)
        top = paragraph(document, escape(row[f"evidence_{language}"]), 46, bottom - 2, 534, font, 8.6,
                        GRAY, 11.4) - 13
    bottom = paragraph(document, escape(text["limits"]), 32, top - 6, 548, font, 8.4, GRAY, 11)
    if bottom < 104:
        raise ValueError("Recommendations exceed their page allocation.")

    # Sources, links and the course credit at the bottom.
    paragraph(document, escape(text["sources"]), 32, 90, 548, font, 7.8, GRAY, 10)
    links = (f'<link href="{FINANCE_URL}" color="#217F80">{text["links"][0]}</link>  |  '
             f'<link href="{SHOPPING_URL}" color="#217F80">{text["links"][1]}</link>')
    paragraph(document, links, 32, 77, 548, "Helvetica", 7.8, TEAL, 10)
    document.setStrokeColor(LIGHT)
    document.line(32, 60, 580, 60)
    if paragraph(document, escape(text["credit"]), 32, 52, 548, font, 7.4, GRAY, 9.4) < 16:
        raise ValueError("Course credit exceeds the bottom margin.")
    document.showPage()
    document.save()


# Pick an embeddable Chinese font when one is available, otherwise use a built-in CID font.
def register_chinese_font():
    pdfmetrics.registerFont(UnicodeCIDFont("STSong-Light"))
    regular = os.environ.get("GENZ_CJK_FONT")
    bold = os.environ.get("GENZ_CJK_BOLD_FONT", regular)
    mac_font = Path("/System/Library/Fonts/Supplemental/Arial Unicode.ttf")
    if not regular and mac_font.is_file():
        regular = bold = str(mac_font)
    if regular:
        pdfmetrics.registerFont(TTFont("ChineseRegular", regular))
        pdfmetrics.registerFont(TTFont("ChineseBold", bold))
        FONTS["zh"] = ("ChineseRegular", "ChineseBold")


def main():
    data = load_results()
    register_chinese_font()
    OUTPUT.mkdir(parents=True, exist_ok=True)
    for language in ["en", "zh"]:
        text = summary_text(language, data)
        write_markdown(language, text, data)
        write_pdf(language, text, data)
    print("Created English and Chinese Markdown summaries and one-page PDFs.")


# Run the export only when called directly.
if __name__ == "__main__":
    main()
