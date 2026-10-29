-- Summarize each rule group and calculate its own ordered medians.
DROP TABLE IF EXISTS finance_segments;
CREATE TABLE finance_segments AS
WITH ordered AS (
    SELECT segment, income, consumption,
           ROW_NUMBER() OVER (PARTITION BY segment ORDER BY income) AS income_position,
           ROW_NUMBER() OVER (PARTITION BY segment ORDER BY consumption) AS consumption_position,
           COUNT(*) OVER (PARTITION BY segment) AS n
    FROM finance_segment_people
), medians AS (
    SELECT segment,
           AVG(CASE WHEN income_position IN ((n + 1) / 2, (n + 2) / 2) THEN income END) AS income_median,
           AVG(CASE WHEN consumption_position IN ((n + 1) / 2, (n + 2) / 2) THEN consumption END) AS consumption_median
    FROM ordered GROUP BY segment
)
SELECT p.segment, COUNT(*) AS n,
       100.0 * COUNT(*) / (SELECT COUNT(*) FROM finance_people) AS sample_pct,
       MIN(income) AS income_min, MAX(income) AS income_max,
       AVG(income) AS income_mean, m.income_median,
       MIN(consumption) AS consumption_min, MAX(consumption) AS consumption_max,
       AVG(consumption) AS consumption_mean, m.consumption_median,
       COUNT(NULLIF(income, 0)) AS n_with_income_ratio,
       COUNT(NULLIF(consumption, 0)) AS n_with_consumption_ratio,
       AVG(1.0 * consumption / NULLIF(income, 0)) AS mean_consumption_income_ratio,
       AVG(self_investment) AS self_investment_mean,
       AVG(enjoyment) AS enjoyment_mean,
       AVG(remaining_consumption) AS remaining_consumption_mean,
       100.0 * AVG(1.0 * self_investment / NULLIF(consumption, 0)) AS mean_person_self_investment_consumption_share_pct,
       100.0 * AVG(1.0 * enjoyment / NULLIF(consumption, 0)) AS mean_person_enjoyment_consumption_share_pct,
       100.0 * AVG(1.0 * remaining_consumption / NULLIF(consumption, 0)) AS mean_person_remaining_consumption_share_pct,
       100.0 * SUM(self_investment) / NULLIF(SUM(consumption), 0) AS aggregate_self_investment_consumption_share_pct,
       100.0 * SUM(enjoyment) / NULLIF(SUM(consumption), 0) AS aggregate_enjoyment_consumption_share_pct,
       100.0 * SUM(remaining_consumption) / NULLIF(SUM(consumption), 0) AS aggregate_remaining_consumption_share_pct,
       AVG(savings) AS savings_mean,
       AVG(investments) AS investments_mean,
       100.0 * AVG(1.0 * savings / NULLIF(income, 0)) AS mean_person_savings_income_share_pct,
       100.0 * AVG(1.0 * investments / NULLIF(income, 0)) AS mean_person_investments_income_share_pct,
       100.0 * AVG(1.0 * savings / NULLIF(allocations_with_savings_investments, 0)) AS mean_person_savings_allocation_share_pct,
       100.0 * AVG(1.0 * investments / NULLIF(allocations_with_savings_investments, 0)) AS mean_person_investments_allocation_share_pct,
       100.0 * SUM(savings) / NULLIF(SUM(allocations_with_savings_investments), 0) AS aggregate_savings_allocation_share_pct,
       100.0 * SUM(investments) / NULLIF(SUM(allocations_with_savings_investments), 0) AS aggregate_investments_allocation_share_pct
FROM finance_segment_people AS p JOIN medians AS m USING (segment)
GROUP BY p.segment;

-- Mean person shares weight each person equally; aggregate shares weight dollars equally.
DROP TABLE IF EXISTS finance_category_shares;
CREATE TABLE finance_category_shares AS
SELECT 'all' AS segment, category, COUNT(*) AS n,
       COUNT(NULLIF(consumption, 0)) AS n_with_consumption_ratio,
       AVG(amount) AS amount_mean, SUM(amount) AS amount_total,
       100.0 * AVG(1.0 * amount / NULLIF(consumption, 0)) AS mean_person_consumption_share_pct,
       100.0 * SUM(amount) / NULLIF(SUM(consumption), 0) AS aggregate_consumption_share_pct
FROM finance_category_amounts GROUP BY category
UNION ALL
SELECT segment, category, COUNT(*), COUNT(NULLIF(consumption, 0)),
       AVG(amount), SUM(amount),
       100.0 * AVG(1.0 * amount / NULLIF(consumption, 0)),
       100.0 * SUM(amount) / NULLIF(SUM(consumption), 0)
FROM finance_category_amounts GROUP BY segment, category;
