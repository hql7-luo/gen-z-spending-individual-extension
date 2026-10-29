-- Calculate centered Pearson correlations to reduce numerical cancellation.
DROP TABLE IF EXISTS finance_core_metrics;
CREATE TABLE finance_core_metrics AS
SELECT COUNT(*) AS n_raw,
       COUNT(*) AS n_included,
       0 AS n_excluded,
       'USD' AS currency,
       'unspecified' AS period,
       'undocumented; appears randomly generated' AS real_or_synthetic_provenance,
       MIN(age) AS age_min,
       MAX(age) AS age_max,
       MIN(income) AS income_min,
       MAX(income) AS income_max,
       AVG(income) AS income_mean,
       s.median_income AS income_median,
       MIN(consumption) AS consumption_min,
       MAX(consumption) AS consumption_max,
       AVG(consumption) AS consumption_mean,
       s.median_consumption AS consumption_median,
       SUM(income) AS income_total,
       SUM(consumption) AS consumption_total,
       SUM(consumption > income) AS consumption_above_income_count,
       100.0 * SUM(consumption > income) / COUNT(*) AS consumption_above_income_pct,
       SUM(consumption = income) AS consumption_equal_income_count,
       SUM(consumption < income) AS consumption_below_income_count,
       COUNT(NULLIF(income, 0)) AS n_with_income_ratio,
       AVG(1.0 * consumption / NULLIF(income, 0)) AS mean_consumption_income_ratio,
       SUM((income - s.mean_income) * (consumption - s.mean_consumption))
       / NULLIF(SQRT(SUM((income - s.mean_income) * (income - s.mean_income))
       * SUM((consumption - s.mean_consumption) * (consumption - s.mean_consumption))), 0)
           AS income_consumption_pearson_r,
       MIN(allocations_with_savings_investments) AS allocations_with_savings_investments_min,
       MAX(allocations_with_savings_investments) AS allocations_with_savings_investments_max,
       AVG(allocations_with_savings_investments) AS allocations_with_savings_investments_mean,
       SUM(allocations_with_savings_investments) AS allocations_with_savings_investments_total,
       SUM(allocations_with_savings_investments > income)
           AS allocations_with_savings_investments_above_income_count,
       100.0 * SUM(allocations_with_savings_investments > income) / COUNT(*)
           AS allocations_with_savings_investments_above_income_pct,
       SUM(allocations_with_savings_investments = income)
           AS allocations_with_savings_investments_equal_income_count,
       SUM((income - s.mean_income) * (allocations_with_savings_investments - s.mean_allocations))
       / NULLIF(SQRT(SUM((income - s.mean_income) * (income - s.mean_income))
       * SUM((allocations_with_savings_investments - s.mean_allocations)
       * (allocations_with_savings_investments - s.mean_allocations))), 0)
           AS income_allocations_with_savings_investments_pearson_r
FROM finance_people CROSS JOIN finance_sample_stats AS s;

-- Compare the report figures with explicitly named denominators and methods.
DROP TABLE IF EXISTS finance_denominator_audit;
CREATE TABLE finance_denominator_audit AS
WITH amounts AS (
    SELECT 'self_investment' AS allocation_group, self_investment AS amount,
           income, consumption, allocations_with_savings_investments
    FROM finance_people
    UNION ALL
    SELECT 'enjoyment', enjoyment, income, consumption, allocations_with_savings_investments
    FROM finance_people
), ratios AS (
    SELECT allocation_group, 'income' AS denominator,
           COUNT(*) AS n, COUNT(NULLIF(income, 0)) AS n_valid_denominator,
           100.0 * AVG(1.0 * amount / NULLIF(income, 0)) AS mean_person_share_pct,
           100.0 * SUM(amount) / NULLIF(SUM(income), 0) AS aggregate_share_pct
    FROM amounts GROUP BY allocation_group
    UNION ALL
    SELECT allocation_group, 'consumption', COUNT(*), COUNT(NULLIF(consumption, 0)),
           100.0 * AVG(1.0 * amount / NULLIF(consumption, 0)),
           100.0 * SUM(amount) / NULLIF(SUM(consumption), 0)
    FROM amounts GROUP BY allocation_group
    UNION ALL
    SELECT allocation_group, 'allocations_with_savings_investments', COUNT(*),
           COUNT(NULLIF(allocations_with_savings_investments, 0)),
           100.0 * AVG(1.0 * amount / NULLIF(allocations_with_savings_investments, 0)),
           100.0 * SUM(amount) / NULLIF(SUM(allocations_with_savings_investments), 0)
    FROM amounts GROUP BY allocation_group
), report_values AS (
    SELECT 'self_investment' AS allocation_group, 'income' AS denominator,
           25 AS report_page, 29.98 AS report_share_pct
    UNION ALL SELECT 'enjoyment', 'income', 25, 31.06
    UNION ALL SELECT 'self_investment', 'allocations_with_savings_investments', 26, 13.48
    UNION ALL SELECT 'enjoyment', 'allocations_with_savings_investments', 26, 14.19
)
SELECT r.*, v.report_page, v.report_share_pct,
       r.mean_person_share_pct - v.report_share_pct AS mean_person_difference_pp,
       CASE WHEN v.report_share_pct IS NULL THEN NULL
            ELSE ROUND(r.mean_person_share_pct, 2) = v.report_share_pct
       END AS reproduces_report_at_2_decimals
FROM ratios AS r
LEFT JOIN report_values AS v USING (allocation_group, denominator);
