# Gen Z spending: re-checking a course project

Individual extension of a UW IS 445 group project (2025)

- **1,700** financial records, ages 18-27
- **0.03** correlation: income vs consumption
- **50.6%** spend more than they earn

Both numbers match the original course presentation. Rebuilt in SQLite and checked independently in Python.

## What the re-check found

1. **The financial data looks randomly generated.** All 14 numeric columns are spread evenly between round limits (income: $1,501 to $7,994), and no two columns correlate above 0.06. The near-zero correlation reflects how the file was built, not how Gen Z spends.

2. **Spending above income is mostly an income effect.** Average consumption is about $4,800 at every income level, so 88% of below-median earners spend more than they earn, versus 14% of everyone else.

3. **Age groups shop the same way (synthetic data).** In a separate synthetic shopping dataset, 0 of 4 comparisons (payment, shipping, frequency, category) differ between ages 18-27 and 28-70 after Holm correction.

Spending more than income, by income decile: D1 100%, D2 99%, D3 94%, D4 84%, D5 61%, D6 39%, D7 21%, D8 8%, D9 0%, D10 0%

## What I would do with real customer data

1. Segment real customers on what they actually buy (category mix, repeat purchases, response to past promotions), not on income or age alone. Income and consumption are unrelated in this file (r = 0.03); average consumption stays between $4,660 and $4,866 in every income decile.

2. Start with one shared offer, then A/B test single changes (price, delivery fee, promotion timing) on small groups before rolling them out. In the synthetic shopping data, 0 of 4 comparisons (payment, shipping, frequency, category) differ between ages 18-27 and 28-70 after correction (Cramer's V at most 0.04).

3. Check where a dataset comes from and how it is distributed before building recommendations on it. A quick distribution check showed every numeric column spread evenly between round limits, with no pair of columns correlated above 0.06.

Limits: the two datasets are separate and never joined; amounts are USD with no stated period; results describe these files, not real Gen Z consumers.

Sources: Financial v1 (2025-01-31, CC0)  |  Shopping v2 (synthetic)

- [Financial dataset](https://www.kaggle.com/datasets/manandkumar/gen-z-money-spending-dataset)
- [Synthetic shopping dataset](https://www.kaggle.com/datasets/iamsouravbanerjee/customer-shopping-trends-dataset)

Course context: UW IS 445 group project, March-June 2025. My role: data analysis and visualization with SQL, Excel and Python. I rebuilt this extension on my own in October 2026, after the original course files were lost.
