"""Reproduce the financial tables with SQLite and verify them with pandas."""

# Import the tools used for source checks, SQLite and independent calculations.
import hashlib
import json
import math
import sqlite3
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import chisquare


# Locate the fixed source and output folders from this script.
ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'data/raw/genz_money_spends.csv'
DATABASE = ROOT / 'data/processed/analysis.sqlite'
TABLES = ROOT / 'outputs/tables'
EXPECTED_SHA256 = '7f11ed0fd2e95de43687d84ad6ee7d575b0c61f7a06d4522bffe15fb6c8dab41'
HEADERS = [
    'ID', 'Age', 'Income (USD)', 'Rent (USD)', 'Groceries (USD)',
    'Eating Out (USD)', 'Entertainment (USD)', 'Subscription Services (USD)',
    'Education (USD)', 'Online Shopping (USD)', 'Savings (USD)',
    'Investments (USD)', 'Travel (USD)', 'Fitness (USD)', 'Miscellaneous (USD)',
]
NAMES = [
    'id', 'age', 'income', 'rent', 'groceries', 'eating_out', 'entertainment',
    'subscription_services', 'education', 'online_shopping', 'savings',
    'investments', 'travel', 'fitness', 'miscellaneous',
]
CATEGORIES = [
    'rent', 'groceries', 'eating_out', 'entertainment', 'subscription_services',
    'education', 'online_shopping', 'travel', 'fitness', 'miscellaneous',
]
PROVENANCE = 'undocumented; appears randomly generated'

# Stop if the source differs from the reviewed data or fails basic checks.
source_hash = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
if source_hash != EXPECTED_SHA256:
    raise ValueError('Source SHA256 differs from the reviewed dataset.')
raw = pd.read_csv(SOURCE)
if list(raw.columns) != HEADERS:
    raise ValueError('Source headers differ from the fixed 15-column schema.')
if raw.shape != (1700, 15):
    raise ValueError(f'Expected 1700 rows and 15 columns; received {raw.shape}.')
raw = raw.apply(pd.to_numeric, errors='raise')
if not np.isfinite(raw.to_numpy()).all():
    raise ValueError('Source contains missing or non-finite values.')
if (raw.to_numpy() < 0).any():
    raise ValueError('Source contains negative values.')
if raw['ID'].nunique() != len(raw) or not (raw['ID'] % 1 == 0).all():
    raise ValueError('Source IDs must be unique whole numbers.')
people = raw.set_axis(NAMES, axis=1).copy()

# Load normalized raw columns; SQL owns all exported financial calculations.
DATABASE.parent.mkdir(parents=True, exist_ok=True)
TABLES.mkdir(parents=True, exist_ok=True)
connection = sqlite3.connect(DATABASE, timeout=60)
connection.create_function('SQRT', 1, math.sqrt, deterministic=True)
people.to_sql('finance_raw', connection, index=False, if_exists='replace')
for filename in ['01_finance_views.sql', '02_core_metrics.sql', '03_segment_profiles.sql',
                 '04_overspend_by_income.sql']:
    connection.executescript((ROOT / 'sql' / filename).read_text())

# Build an independent pandas calculation directly from normalized raw columns.
people['consumption'] = people[CATEGORIES].sum(axis=1)
people['allocations_with_savings_investments'] = (
    people[CATEGORIES + ['savings', 'investments']].sum(axis=1)
)
people['self_investment'] = people[['education', 'fitness']].sum(axis=1)
people['enjoyment'] = people[['travel', 'entertainment']].sum(axis=1)
people['remaining_consumption'] = people[
    ['rent', 'groceries', 'eating_out', 'subscription_services', 'online_shopping', 'miscellaneous']
].sum(axis=1)
median_income = people['income'].median()
people['segment'] = np.where(
    people['income'] < median_income, 'lower_income_', 'higher_income_'
)
people['segment'] += np.where(
    people['consumption'] > people['income'], 'above_income', 'not_above_income'
)

# Compare every numeric table field, with a tolerance for floating point arithmetic.
verified_tables = []


def verify_table(name, expected, keys):
    actual = pd.read_sql_query(f'SELECT * FROM {name}', connection)
    actual = actual.set_index(keys).sort_index()
    expected = pd.DataFrame(expected).set_index(keys).sort_index()
    if set(actual.columns) != set(expected.columns):
        raise AssertionError(f'{name}: exported and independent columns differ.')
    pd.testing.assert_frame_equal(
        actual, expected[actual.columns], check_dtype=False, check_exact=False,
        rtol=1e-10, atol=1e-9, obj=f'{name}: SQL versus independent pandas',
    )
    verified_tables.append(name)


# Independently verify the main result and separately named allocation sensitivity.
income = people['income']
consumption = people['consumption']
allocations = people['allocations_with_savings_investments']
core_expected = {
    'n_raw': len(raw), 'n_included': len(people), 'n_excluded': 0,
    'currency': 'USD', 'period': 'unspecified', 'real_or_synthetic_provenance': PROVENANCE,
    'age_min': people['age'].min(), 'age_max': people['age'].max(),
    'income_min': income.min(), 'income_max': income.max(),
    'income_mean': income.mean(), 'income_median': income.median(),
    'consumption_min': consumption.min(), 'consumption_max': consumption.max(),
    'consumption_mean': consumption.mean(), 'consumption_median': consumption.median(),
    'income_total': income.sum(), 'consumption_total': consumption.sum(),
    'consumption_above_income_count': (consumption > income).sum(),
    'consumption_above_income_pct': (consumption > income).mean() * 100,
    'consumption_equal_income_count': (consumption == income).sum(),
    'consumption_below_income_count': (consumption < income).sum(),
    'n_with_income_ratio': income.ne(0).sum(),
    'mean_consumption_income_ratio': (consumption / income.replace(0, np.nan)).mean(),
    'income_consumption_pearson_r': np.corrcoef(income, consumption)[0, 1],
    'allocations_with_savings_investments_min': allocations.min(),
    'allocations_with_savings_investments_max': allocations.max(),
    'allocations_with_savings_investments_mean': allocations.mean(),
    'allocations_with_savings_investments_total': allocations.sum(),
    'allocations_with_savings_investments_above_income_count': (allocations > income).sum(),
    'allocations_with_savings_investments_above_income_pct': (allocations > income).mean() * 100,
    'allocations_with_savings_investments_equal_income_count': (allocations == income).sum(),
    'income_allocations_with_savings_investments_pearson_r': np.corrcoef(income, allocations)[0, 1],
}
verify_table('finance_core_metrics', [core_expected], ['n_raw'])

# Independently verify each group, including medians and ratio denominators.
segment_expected = []
category_expected = []
for segment, group in people.groupby('segment', sort=True):
    group_income = group['income'].replace(0, np.nan)
    group_consumption = group['consumption'].replace(0, np.nan)
    group_allocations = group['allocations_with_savings_investments'].replace(0, np.nan)
    row = {
        'segment': segment, 'n': len(group), 'sample_pct': 100 * len(group) / len(people),
        'income_min': group['income'].min(), 'income_max': group['income'].max(),
        'income_mean': group['income'].mean(), 'income_median': group['income'].median(),
        'consumption_min': group['consumption'].min(), 'consumption_max': group['consumption'].max(),
        'consumption_mean': group['consumption'].mean(),
        'consumption_median': group['consumption'].median(),
        'n_with_income_ratio': group_income.notna().sum(),
        'n_with_consumption_ratio': group_consumption.notna().sum(),
        'mean_consumption_income_ratio': (group['consumption'] / group_income).mean(),
    }
    for column in ['self_investment', 'enjoyment', 'remaining_consumption']:
        row[f'{column}_mean'] = group[column].mean()
        share_name = column if column == 'remaining_consumption' else f'{column}_consumption'
        row[f'mean_person_{share_name}_share_pct'] = (group[column] / group_consumption).mean() * 100
        row[f'aggregate_{share_name}_share_pct'] = group[column].sum() / group['consumption'].sum() * 100
    for column in ['savings', 'investments']:
        row[f'{column}_mean'] = group[column].mean()
        row[f'mean_person_{column}_income_share_pct'] = (group[column] / group_income).mean() * 100
        row[f'mean_person_{column}_allocation_share_pct'] = (group[column] / group_allocations).mean() * 100
        row[f'aggregate_{column}_allocation_share_pct'] = group[column].sum() / group_allocations.sum() * 100
    segment_expected.append(row)
verify_table('finance_segments', segment_expected, ['segment'])

# Independently verify equal-person and equal-dollar category shares.
for segment, group in [('all', people)] + list(people.groupby('segment', sort=True)):
    for category in CATEGORIES:
        category_expected.append({
            'segment': segment, 'category': category, 'n': len(group),
            'n_with_consumption_ratio': group['consumption'].ne(0).sum(),
            'amount_mean': group[category].mean(), 'amount_total': group[category].sum(),
            'mean_person_consumption_share_pct': (
                group[category] / group['consumption'].replace(0, np.nan)
            ).mean() * 100,
            'aggregate_consumption_share_pct': group[category].sum() / group['consumption'].sum() * 100,
        })
verify_table('finance_category_shares', category_expected, ['segment', 'category'])

# Reproduce the report's displayed percentages only where the calculations agree.
report_values = {
    ('self_investment', 'income'): (25, 29.98),
    ('enjoyment', 'income'): (25, 31.06),
    ('self_investment', 'allocations_with_savings_investments'): (26, 13.48),
    ('enjoyment', 'allocations_with_savings_investments'): (26, 14.19),
}
denominator_expected = []
for allocation_group in ['self_investment', 'enjoyment']:
    for denominator in ['income', 'consumption', 'allocations_with_savings_investments']:
        denominator_values = people[denominator].replace(0, np.nan)
        person_share = (people[allocation_group] / denominator_values).mean() * 100
        page, reported = report_values.get((allocation_group, denominator), (np.nan, np.nan))
        denominator_expected.append({
            'allocation_group': allocation_group, 'denominator': denominator,
            'n': len(people), 'n_valid_denominator': denominator_values.notna().sum(),
            'mean_person_share_pct': person_share,
            'aggregate_share_pct': people[allocation_group].sum() / people[denominator].sum() * 100,
            'report_page': page, 'report_share_pct': reported,
            'mean_person_difference_pp': person_share - reported,
            'reproduces_report_at_2_decimals': (
                np.nan if pd.isna(reported) else int(round(person_share, 2) == reported)
            ),
        })
verify_table('finance_denominator_audit', denominator_expected, ['allocation_group', 'denominator'])

# Independently verify the overspending share for income halves and income deciles.
overspend_expected = []
by_income = people.sort_values(['income', 'id'], kind='stable').reset_index(drop=True)
by_income['income_half'] = np.where(by_income['income'] < median_income, 'below_median', 'at_or_above_median')
by_income['income_decile'] = 0
for number, positions in enumerate(np.array_split(np.arange(len(by_income)), 10), start=1):
    by_income.loc[positions, 'income_decile'] = number
by_income['income_decile'] = by_income['income_decile'].map(lambda number: f'd{number:02d}')
for grouping, column in [('income_half', 'income_half'), ('income_decile', 'income_decile')]:
    for label, group in by_income.groupby(column, sort=True):
        above = group['consumption'] > group['income']
        overspend_expected.append({
            'grouping': grouping, 'income_group': label, 'n': len(group),
            'income_min': group['income'].min(), 'income_max': group['income'].max(),
            'income_mean': group['income'].mean(), 'consumption_mean': group['consumption'].mean(),
            'above_income_count': int(above.sum()), 'above_income_pct': above.mean() * 100,
        })
verify_table('finance_overspend_by_income', overspend_expected, ['grouping', 'income_group'])

# Check whether each numeric column looks like an even spread between round limits.
generation_rows = []
for header, name in zip(HEADERS[1:], NAMES[1:]):
    values = people[name]
    counts, _ = np.histogram(values, bins=10, range=(values.min(), values.max() + 1))
    generation_rows.append({
        'column': header, 'min': values.min(), 'max': values.max(),
        'mean': values.mean(), 'median': values.median(), 'skewness': values.skew(),
        'smallest_bin_count': counts.min(), 'largest_bin_count': counts.max(),
        'uniform_chi_square_p': chisquare(counts).pvalue,
    })
generation = pd.DataFrame(generation_rows)
pair_correlations = people[NAMES[1:]].corr().abs().to_numpy().copy()
np.fill_diagonal(pair_correlations, 0)
max_pair_correlation = float(pair_correlations.max())
generation_summary = {
    'columns_tested': len(generation),
    'bins_per_column': 10,
    'columns_rejecting_uniform_at_0_05': int((generation['uniform_chi_square_p'] < 0.05).sum()),
    'max_abs_pairwise_correlation': max_pair_correlation,
    'reading': 'Every numeric column is close to an even spread between round limits and no two columns move together, which fits independent random draws better than survey data.',
}
generation.to_csv(TABLES / 'finance_generation_check.csv', index=False, float_format='%.15g')

# Check the reviewed headline and accounting identities using the real source.
np.testing.assert_allclose(core_expected['income_consumption_pearson_r'], 0.03008187006506225, rtol=0, atol=1e-14)
if core_expected['consumption_above_income_count'] != 860:
    raise AssertionError('The reviewed count of 860 rows was not reproduced.')
if core_expected['consumption_equal_income_count'] != 0:
    raise AssertionError('Unexpected rows with equal income and consumption.')
if sum(row['n'] for row in segment_expected) != 1700:
    raise AssertionError('The four groups do not partition all source rows.')
np.testing.assert_allclose(
    people['self_investment'] + people['enjoyment'] + people['remaining_consumption'], consumption,
)
shares = pd.DataFrame(category_expected).groupby('segment')[
    ['mean_person_consumption_share_pct', 'aggregate_consumption_share_pct']
].sum()
np.testing.assert_allclose(shares.to_numpy(), 100, rtol=0, atol=1e-10)

# Save the source and denominator checks alongside the calculated results.
quality_rows = [
    ['source_sha256', source_hash, EXPECTED_SHA256, 1],
    ['row_count', len(raw), 1700, 1],
    ['column_count', len(raw.columns), 15, 1],
    ['unique_ids', people['id'].nunique(), 1700, 1],
    ['null_cells', int(raw.isna().sum().sum()), 0, 1],
    ['non_finite_cells', int((~np.isfinite(raw.to_numpy())).sum()), 0, 1],
    ['negative_cells', int((raw.to_numpy() < 0).sum()), 0, 1],
    ['zero_income_rows', int(income.eq(0).sum()), 0, 1],
    ['zero_consumption_rows', int(consumption.eq(0).sum()), 0, 1],
    ['excluded_rows', 0, 0, 1],
    ['segment_count_sum', sum(row['n'] for row in segment_expected), 1700, 1],
    ['independently_verified_sql_tables', len(verified_tables), 5, 1],
    ['income_halves_partition_rows', sum(row['n'] for row in overspend_expected if row['grouping'] == 'income_half'), 1700, 1],
    ['income_deciles_partition_rows', sum(row['n'] for row in overspend_expected if row['grouping'] == 'income_decile'), 1700, 1],
]
if any(observed != expected for _, observed, expected, _ in quality_rows[1:]):
    raise AssertionError('A source or partition check failed.')
quality = pd.DataFrame(quality_rows, columns=['check', 'observed', 'expected', 'passed'])
quality.to_sql('finance_quality', connection, index=False, if_exists='replace')
connection.commit()

# Export deterministic tables; all amounts are USD over an unspecified period.
exports = {}
for name in [
    'finance_core_metrics', 'finance_segments', 'finance_category_shares',
    'finance_quality', 'finance_denominator_audit', 'finance_overspend_by_income',
]:
    result = pd.read_sql_query(f'SELECT * FROM {name}', connection)
    if name == 'finance_overspend_by_income':
        result = result.sort_values(['grouping', 'income_group'], kind='stable').reset_index(drop=True)
    elif name == 'finance_segments':
        result = result.sort_values('segment', kind='stable').reset_index(drop=True)
    elif name == 'finance_category_shares':
        result = result.sort_values(['segment', 'category'], kind='stable').reset_index(drop=True)
    elif name == 'finance_denominator_audit':
        result = result.sort_values(['allocation_group', 'denominator'], kind='stable').reset_index(drop=True)
    result.to_csv(TABLES / f'{name}.csv', index=False, float_format='%.15g')
    exports[name] = result.astype(object).where(pd.notna(result), None).to_dict(orient='records')
results = {
    'source_file': 'data/raw/genz_money_spends.csv',
    'source_sha256': source_hash,
    'currency': 'USD',
    'period': 'unspecified',
    'real_or_synthetic_provenance': PROVENANCE,
    'data_generation_check': generation_summary,
    'consumption_categories': CATEGORIES,
    'consumption_definition': 'Sum of the ten consumption categories; excludes savings and investments.',
    'allocation_sensitivity_definition': 'Consumption plus savings and investments.',
    'segment_income_threshold': float(median_income),
    'segment_rule': 'Income below sample median versus at or above median, crossed with consumption above income versus at or below income.',
    'grouping_definitions': {
        'self_investment': ['education', 'fitness'],
        'enjoyment': ['travel', 'entertainment'],
        'remaining_consumption': ['rent', 'groceries', 'eating_out', 'subscription_services', 'online_shopping', 'miscellaneous'],
    },
    'share_methods': {
        'mean_person': 'Mean of each included person amount divided by that person denominator.',
        'aggregate': 'Sum of amounts divided by sum of denominators.',
        'pct': 'Percent; multiply the underlying ratio by 100.',
    },
    'limits': [
        'The publisher does not document how the data were collected; the distribution check suggests random generation.',
        'The amount period is not stated, so income and consumption are compared as recorded.',
        'Results describe this file, not real Gen Z consumers.',
    ],
    'verification': {
        'method': 'Independent pandas and numpy recomputation from the source columns.',
        'numeric_relative_tolerance': 1e-10,
        'numeric_absolute_tolerance': 1e-9,
        'verified_tables': verified_tables,
        'all_checks_passed': True,
    },
    **exports,
}
(TABLES / 'finance_results.json').write_text(json.dumps(results, indent=2, allow_nan=False) + '\n')
connection.close()
print(json.dumps({
    'rows_included': len(people), 'rows_excluded': 0,
    'income_consumption_pearson_r': float(core_expected['income_consumption_pearson_r']),
    'consumption_above_income_count': int(core_expected['consumption_above_income_count']),
    'consumption_above_income_pct': float(core_expected['consumption_above_income_pct']),
    'max_abs_pairwise_correlation': max_pair_correlation,
    'columns_rejecting_uniform_at_0_05': generation_summary['columns_rejecting_uniform_at_0_05'],
    'verified_sql_tables': verified_tables,
    'output_files': [f'{name}.csv' for name in exports] + ['finance_generation_check.csv', 'finance_results.json'],
}, indent=2))
