-- Separate consumption from savings and investments.
DROP VIEW IF EXISTS finance_category_amounts;
DROP VIEW IF EXISTS finance_segment_people;
DROP VIEW IF EXISTS finance_sample_stats;
DROP VIEW IF EXISTS finance_people;

CREATE VIEW finance_people AS
SELECT *,
       rent + groceries + eating_out + entertainment + subscription_services
       + education + online_shopping + travel + fitness + miscellaneous AS consumption,
       rent + groceries + eating_out + entertainment + subscription_services
       + education + online_shopping + travel + fitness + miscellaneous
       + savings + investments AS allocations_with_savings_investments,
       education + fitness AS self_investment,
       travel + entertainment AS enjoyment,
       rent + groceries + eating_out + subscription_services
       + online_shopping + miscellaneous AS remaining_consumption
FROM finance_raw;

-- Use the average of the middle two ordered values as the sample median.
CREATE VIEW finance_sample_stats AS
WITH ordered AS (
    SELECT income, consumption,
           ROW_NUMBER() OVER (ORDER BY income) AS income_position,
           ROW_NUMBER() OVER (ORDER BY consumption) AS consumption_position,
           COUNT(*) OVER () AS n
    FROM finance_people
)
SELECT COUNT(*) AS n,
       AVG(income) AS mean_income,
       AVG(consumption) AS mean_consumption,
       (SELECT AVG(income) FROM ordered
        WHERE income_position IN ((n + 1) / 2, (n + 2) / 2)) AS median_income,
       (SELECT AVG(consumption) FROM ordered
        WHERE consumption_position IN ((n + 1) / 2, (n + 2) / 2)) AS median_consumption,
       AVG(allocations_with_savings_investments) AS mean_allocations
FROM finance_people;

-- These four groups are descriptive rules, not discovered consumer preferences.
CREATE VIEW finance_segment_people AS
SELECT p.*,
       CASE
           WHEN income < s.median_income AND consumption > income
               THEN 'lower_income_above_income'
           WHEN income < s.median_income AND consumption <= income
               THEN 'lower_income_not_above_income'
           WHEN income >= s.median_income AND consumption > income
               THEN 'higher_income_above_income'
           ELSE 'higher_income_not_above_income'
       END AS segment
FROM finance_people AS p CROSS JOIN finance_sample_stats AS s;

-- Put the ten consumption categories into one long table.
CREATE VIEW finance_category_amounts AS
SELECT id, segment, consumption, 'rent' AS category, rent AS amount FROM finance_segment_people
UNION ALL SELECT id, segment, consumption, 'groceries', groceries FROM finance_segment_people
UNION ALL SELECT id, segment, consumption, 'eating_out', eating_out FROM finance_segment_people
UNION ALL SELECT id, segment, consumption, 'entertainment', entertainment FROM finance_segment_people
UNION ALL SELECT id, segment, consumption, 'subscription_services', subscription_services FROM finance_segment_people
UNION ALL SELECT id, segment, consumption, 'education', education FROM finance_segment_people
UNION ALL SELECT id, segment, consumption, 'online_shopping', online_shopping FROM finance_segment_people
UNION ALL SELECT id, segment, consumption, 'travel', travel FROM finance_segment_people
UNION ALL SELECT id, segment, consumption, 'fitness', fitness FROM finance_segment_people
UNION ALL SELECT id, segment, consumption, 'miscellaneous', miscellaneous FROM finance_segment_people;
