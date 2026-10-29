-- Show how the share of people spending above income changes with income.
DROP TABLE IF EXISTS finance_overspend_by_income;
CREATE TABLE finance_overspend_by_income AS
WITH ranked AS (
    SELECT p.id, p.income, p.consumption, s.median_income,
           NTILE(10) OVER (ORDER BY p.income, p.id) AS income_decile
    FROM finance_people AS p CROSS JOIN finance_sample_stats AS s
)
-- Two halves split at the sample median income.
SELECT 'income_half' AS grouping,
       CASE WHEN income < median_income THEN 'below_median' ELSE 'at_or_above_median' END AS income_group,
       COUNT(*) AS n,
       MIN(income) AS income_min,
       MAX(income) AS income_max,
       AVG(income) AS income_mean,
       AVG(consumption) AS consumption_mean,
       SUM(CASE WHEN consumption > income THEN 1 ELSE 0 END) AS above_income_count,
       100.0 * SUM(CASE WHEN consumption > income THEN 1 ELSE 0 END) / COUNT(*) AS above_income_pct
FROM ranked
GROUP BY 1, 2
UNION ALL
-- Ten equal-sized income groups, from lowest to highest income.
SELECT 'income_decile' AS grouping,
       printf('d%02d', income_decile) AS income_group,
       COUNT(*) AS n,
       MIN(income) AS income_min,
       MAX(income) AS income_max,
       AVG(income) AS income_mean,
       AVG(consumption) AS consumption_mean,
       SUM(CASE WHEN consumption > income THEN 1 ELSE 0 END) AS above_income_count,
       100.0 * SUM(CASE WHEN consumption > income THEN 1 ELSE 0 END) / COUNT(*) AS above_income_pct
FROM ranked
GROUP BY 1, 2;
