# Gen Z spending: profiles to test

Independent extension of a UW IS 445 course group project

- **1,700**: financial records | ages 18-27
- **0.0301**: Pearson r: income vs consumption
- **50.59%**: consumption > income

Consumption sums ten categories and excludes savings/investments. Mean individual consumption shares: education + fitness 23.81%; travel + entertainment 25.21%. These are analyst-defined groupings.

## Four designed financial groups | one marketing test each

Lower income < sample median $4,743; higher income >= median. Crossed with consumption > income versus <= income. No natural clusters are claimed.

| Group and rule | n (%) | Mean income / consumption (USD, period unknown) | Test hypothesis |
| --- | ---: | ---: | --- |
| A: Lower income; consumption > income<br>`lower_income_above_income` | 745 (43.82%) | $2,995 / $4,949 | Test a small, one-time starter bundle with its full price visible before checkout. |
| B: Lower income; consumption <= income<br>`lower_income_not_above_income` | 104 (6.12%) | $4,115 / $3,480 | Test an optional low-entry education or fitness trial without automatic renewal. |
| C: Higher income; consumption > income<br>`higher_income_above_income` | 115 (6.76%) | $5,387 / $5,997 | Test a fixed-total-price education and fitness bundle, without installment or credit messaging. |
| D: Higher income; consumption <= income<br>`higher_income_not_above_income` | 736 (43.29%) | $6,550 / $4,664 | Test an optional experience upgrade alongside a clearly priced standard offer. |

## Separate shopping check | synthetic learning data

Age 18-27: n=723; age 28-70: n=3,177. Payment, shipping, frequency and category: 0/4 comparisons have Holm-adjusted p < 0.05 (adjusted p 0.768-1.000; Cramer's V 0.022-0.044). This is a method demonstration, not evidence for real-customer targeting.

## Interpretation limits

Financial sampling, collection period and real-versus-synthetic origin are unknown. USD amounts have no documented time unit. Shopping data are synthetic; the two samples are not joined. Correlation is not causation. Test suggestions are hypotheses, with no measured effectiveness or established preference differences.

Sources: Financial v1 (2025-01-31, CC0) | Shopping v2 (synthetic)

- [Gen Z Money Spending Dataset](https://www.kaggle.com/datasets/manandkumar/gen-z-money-spending-dataset)
- [Customer Shopping Trends Dataset](https://www.kaggle.com/datasets/iamsouravbanerjee/customer-shopping-trends-dataset)

Course context: March-June 2025 group project. hql7-luo's original role: SQL/Excel/Python data analysis and visualization. This individual extension re-runs the analysis with explicit definitions, rule groups and separate age comparisons.
