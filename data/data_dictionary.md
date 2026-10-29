# Financial data dictionary

All 1,700 records are retained. The CSV contains no missing cells, duplicate rows, duplicate IDs or nonpositive income values. Monetary periods and observed-versus-synthetic status are not documented by the publisher.

| Original field | Observed minimum | Observed maximum | Interpretation |
| --- | ---: | ---: | --- |
| ID | 1 | 1700 | Source record identifier, not a cross-source join key |
| Age | 18 | 27 | Age in source, collection year unknown |
| Income (USD) | 1501 | 7994 | Income, period unspecified |
| Rent (USD) | 300 | 1999 | Consumption |
| Groceries (USD) | 100 | 599 | Consumption |
| Eating Out (USD) | 50 | 499 | Consumption |
| Entertainment (USD) | 20 | 399 | Consumption |
| Subscription Services (USD) | 10 | 99 | Consumption |
| Education (USD) | 0 | 1996 | Consumption |
| Online Shopping (USD) | 20 | 699 | Consumption |
| Savings (USD) | 100 | 2999 | Financial allocation, excluded from consumption |
| Investments (USD) | 0 | 4999 | Financial allocation, excluded from consumption |
| Travel (USD) | 53 | 1998 | Consumption |
| Fitness (USD) | 10 | 299 | Consumption |
| Miscellaneous (USD) | 20 | 399 | Consumption; contents unspecified |

## Derived measures

- **Consumption:** the sum of the ten consumption fields above. Savings and investments are excluded. This definition reproduces the presentation's r and percentage above income.
- **All allocations:** consumption + savings + investments. Used only for a clearly labelled denominator audit.
- **Spending above income:** consumption strictly greater than income. Equal values are counted separately.
- **Self-investment:** education + fitness, preserving the course's analyst-defined grouping. It does not measure attitudes or long-term returns.
- **Enjoyment:** travel + entertainment, preserving the course's analyst-defined grouping.
- **Mean individual share:** average of each person's category / denominator. Each person receives equal weight.
- **Aggregate share:** sum of category amounts / sum of denominator amounts. This weights people by the denominator amount.
- **Income segment:** below the sample median or at/above it. The labels describe this sample, not a poverty threshold.
- **Financial rule segment:** income segment crossed with spending above income. These are designed rules, not discovered natural clusters.

## Shopping fields used

Customer ID, Age, Category, Purchase Amount (USD), Review Rating, Shipping Type, Payment Method and Frequency of Purchases are retained for the separate shopping analysis. The source's preferred-payment interpretation and synthetic status are documented in [README](README.md).

`Fortnightly` and `Bi-Weekly` are grouped as `Bi-weekly`; `Quarterly` and `Every 3 Months` are grouped as `Quarterly`. Original labels remain in the local source. The age comparison is 18-27 versus 28-70; the source does not establish survey-year generation labels.
