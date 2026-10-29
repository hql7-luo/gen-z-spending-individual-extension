"""Compare age groups in a separate, explicitly synthetic shopping dataset."""

# Import the small set of tools used to read data, run SQL, and compare groups.
import argparse
import hashlib
import json
import math
from pathlib import Path
import sqlite3
import sys

import pandas as pd
from scipy.stats import chi2_contingency


# Locate project folders without depending on the current working directory.
ROOT = Path(__file__).resolve().parents[1]
SOURCE_URL = "https://www.kaggle.com/datasets/iamsouravbanerjee/customer-shopping-trends-dataset"
DOWNLOAD_URL = (
    "https://www.kaggle.com/api/v1/datasets/download/"
    "iamsouravbanerjee/customer-shopping-trends-dataset?datasetVersionNumber=2"
)
AGE_GROUPS = ["18-27", "28-70"]


# Adjust the four prespecified p values together using the Holm procedure.
def holm_adjust(p_values):
    order = sorted(range(len(p_values)), key=lambda position: p_values[position])
    adjusted = [0.0] * len(p_values)
    previous = 0.0
    for rank, position in enumerate(order):
        candidate = (len(p_values) - rank) * p_values[position]
        previous = max(previous, min(1.0, candidate))
        adjusted[position] = previous
    return adjusted


# Keep this script local-only and explain how to obtain the required input.
def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input", type=Path,
        default=ROOT / "data/raw/shopping_trends_updated.csv",
        help="Local shopping CSV from the pinned Kaggle version 2 archive.",
    )
    args = parser.parse_args()
    if not args.input.is_file():
        print("Shopping analysis was not run: the local CSV is missing.", file=sys.stderr)
        print("Download version 2 from: " + DOWNLOAD_URL, file=sys.stderr)
        print("Extract shopping_trends_updated.csv into data/raw/.", file=sys.stderr)
        print("Raw shopping data are excluded from the public repository.", file=sys.stderr)
        return 1

    # Check the downloaded file against the recorded version before analysis.
    metadata = json.loads((ROOT / "data/shopping_metadata_v2.json").read_text())
    file_hash = hashlib.sha256(args.input.read_bytes()).hexdigest()
    recovered_files = metadata["_local_recovery"]["files"]
    if args.input.name not in recovered_files:
        raise ValueError("Use one of the two recorded shopping CSV filenames.")
    if file_hash != recovered_files[args.input.name]["sha256"]:
        raise ValueError("The shopping CSV does not match the pinned version 2 SHA-256.")
    raw = pd.read_csv(args.input)
    original_fields = list(raw.columns)

    # Use preferred payment consistently across the two supplied CSV variants.
    payment_field = (
        "Preferred Payment Method" if "Preferred Payment Method" in raw.columns
        else "Payment Method"
    )
    field_map = {
        "Customer ID": "customer_id", "Age": "age",
        "Review Rating": "review_rating", "Shipping Type": "shipping",
        "Frequency of Purchases": "frequency_original", "Category": "category",
        payment_field: "payment",
    }
    missing_fields = sorted(set(field_map) - set(raw.columns))
    if missing_fields:
        raise ValueError("Required shopping fields are missing: " + str(missing_fields))
    shopping = raw[list(field_map)].rename(columns=field_map).copy()
    for field in ["customer_id", "age", "review_rating"]:
        shopping[field] = pd.to_numeric(shopping[field], errors="raise")

    # Report quality issues explicitly and do not silently remove any records.
    quality = {
        "missing_cells_all_fields": int(raw.isna().sum().sum()),
        "missing_cells_required_fields": int(shopping.isna().sum().sum()),
        "duplicate_rows": int(raw.duplicated().sum()),
        "duplicate_customer_ids": int(shopping.customer_id.duplicated().sum()),
        "age_min": int(shopping.age.min()),
        "age_max": int(shopping.age.max()),
        "excluded_rows": 0,
    }
    if quality["missing_cells_required_fields"] or quality["duplicate_customer_ids"]:
        raise ValueError("Missing values or repeated customer IDs require review.")
    if not shopping.age.between(18, 70).all():
        raise ValueError("Ages outside the prespecified 18-70 range require review.")

    # Define age groups in advance and combine the stated frequency synonyms.
    shopping["age_group"] = shopping.age.apply(lambda age: "18-27" if age <= 27 else "28-70")
    frequency_mapping = {
        "Fortnightly": "Every 2 weeks", "Bi-Weekly": "Every 2 weeks",
        "Quarterly": "Every 3 months", "Every 3 Months": "Every 3 months",
    }
    shopping["frequency"] = shopping.frequency_original.replace(frequency_mapping)
    output_dir = ROOT / "outputs/tables"
    output_dir.mkdir(parents=True, exist_ok=True)
    database = ROOT / "data/processed/shopping.sqlite"
    database.parent.mkdir(parents=True, exist_ok=True)

    # Store shopping records separately from the unrelated financial sample.
    connection = sqlite3.connect(database)
    shopping.to_sql("shopping", connection, if_exists="replace", index=False)
    profile = pd.read_sql_query(
        """
        SELECT age_group, COUNT(*) AS n,
               AVG(review_rating) AS mean_review_rating
        FROM shopping
        GROUP BY age_group
        ORDER BY age_group
        """, connection,
    )
    if list(profile.age_group) != AGE_GROUPS:
        raise ValueError("Both prespecified age groups must be present.")
    profile.to_csv(output_dir / "shopping_age_group_summary.csv", index=False)

    # Prespecify all four categorical comparisons before calculating p values.
    preference_fields = ["payment", "shipping", "frequency", "category"]
    test_results = []
    preference_tables = []
    for preference in preference_fields:
        counts = pd.read_sql_query(
            f"""
            SELECT age_group, {preference} AS preference_value, COUNT(*) AS n,
                   SUM(COUNT(*)) OVER (PARTITION BY age_group) AS group_n,
                   1.0 * COUNT(*) /
                       SUM(COUNT(*)) OVER (PARTITION BY age_group) AS proportion
            FROM shopping
            GROUP BY age_group, {preference}
            ORDER BY age_group, {preference}
            """, connection,
        )
        counts["percent"] = 100 * counts.proportion
        counts.insert(0, "preference", preference)
        preference_tables.append(counts)

        # Export both the SQL counts and within-age-group proportions.
        contingency = counts.pivot(
            index="preference_value", columns="age_group", values="n"
        ).reindex(columns=AGE_GROUPS).fillna(0).astype(int)
        independently_counted = pd.crosstab(
            shopping[preference], shopping.age_group,
        ).reindex(columns=AGE_GROUPS)
        pd.testing.assert_frame_equal(
            contingency.sort_index(), independently_counted.sort_index(),
            check_names=False,
        )
        contingency.to_csv(output_dir / f"shopping_{preference}_counts.csv")
        proportions = contingency.div(contingency.sum(axis=0), axis=1)
        if not proportions.sum(axis=0).sub(1).abs().lt(1e-12).all():
            raise AssertionError("Within-age-group proportions must sum to one.")
        proportions.to_csv(output_dir / f"shopping_{preference}_proportions.csv")

        # Use chi-square for categorical outcomes and report the effect size.
        chi_square, p_value, degrees_freedom, expected = chi2_contingency(
            contingency.to_numpy().T, correction=False,
        )
        total = int(contingency.to_numpy().sum())
        cramer_v = math.sqrt(chi_square / (total * min(
            contingency.shape[0] - 1, contingency.shape[1] - 1,
        )))
        test_results.append({
            "preference": preference,
            "n": total,
            "chi_square": float(chi_square),
            "degrees_freedom": int(degrees_freedom),
            "minimum_expected_count": float(expected.min()),
            "expected_counts_at_least_5": bool((expected >= 5).all()),
            "p_raw": float(p_value),
            "cramers_v": float(cramer_v),
        })

    # Apply one correction across the four planned comparisons, including null results.
    adjusted_p_values = holm_adjust([result["p_raw"] for result in test_results])
    for result, adjusted_p in zip(test_results, adjusted_p_values):
        result["p_holm"] = adjusted_p
        result["significant_after_holm_0_05"] = adjusted_p < 0.05
    pd.DataFrame(test_results).to_csv(output_dir / "shopping_tests.csv", index=False)
    preferences = pd.concat(preference_tables, ignore_index=True)
    preferences.to_csv(output_dir / "shopping_preferences.csv", index=False)

    # Retain the original frequency labels so their normalization is auditable.
    original_frequency = pd.read_sql_query(
        """
        SELECT age_group, frequency_original AS preference_value, COUNT(*) AS n,
               100.0 * COUNT(*) /
                   SUM(COUNT(*)) OVER (PARTITION BY age_group) AS percent
        FROM shopping
        GROUP BY age_group, frequency_original
        ORDER BY age_group, frequency_original
        """, connection,
    )
    original_frequency.to_csv(output_dir / "shopping_frequency_original.csv", index=False)

    # Keep the report's stated ages 13-28 as a separate replication diagnostic.
    report_profile = pd.read_sql_query(
        """
        SELECT COUNT(*) AS n, MIN(age) AS observed_age_min,
               MAX(age) AS observed_age_max, AVG(review_rating) AS mean_review_rating
        FROM shopping
        WHERE age BETWEEN 13 AND 28
        """, connection,
    )
    report_tables = []
    for preference in preference_fields + ["frequency_original"]:
        report_counts = pd.read_sql_query(
            f"""
            SELECT {preference} AS preference_value, COUNT(*) AS n,
                   SUM(COUNT(*)) OVER () AS group_n,
                   1.0 * COUNT(*) / SUM(COUNT(*)) OVER () AS proportion
            FROM shopping
            WHERE age BETWEEN 13 AND 28
            GROUP BY {preference}
            ORDER BY {preference}
            """, connection,
        )
        report_counts.insert(0, "preference", preference)
        report_counts["percent"] = 100 * report_counts.proportion
        report_tables.append(report_counts)
    report_preferences = pd.concat(report_tables, ignore_index=True)
    report_profile.to_csv(output_dir / "shopping_report_definition_summary.csv", index=False)
    report_preferences.to_csv(output_dir / "shopping_report_definition_preferences.csv", index=False)
    connection.close()

    # Compare the reported rating using the fixed age proxy, without changing cutoffs.
    young_profile = profile.loc[profile.age_group == "18-27"].iloc[0]
    young_preferences = preferences.loc[preferences.age_group == "18-27"]
    shipping = young_preferences.loc[young_preferences.preference == "shipping"]
    frequency = young_preferences.loc[young_preferences.preference == "frequency"]
    raw_frequency = original_frequency.loc[original_frequency.age_group == "18-27"]
    course_comparisons = {
        "review_rating": {
            "course_displayed": 3.79,
            "recovered_mean": float(young_profile.mean_review_rating),
            "recovered_rounded_2dp": round(float(young_profile.mean_review_rating), 2),
            "matches_at_reported_precision": round(float(young_profile.mean_review_rating), 2) == 3.79,
        },
        "shipping_17_5_percent": {
            "course_displayed_percent": 17.5,
            "reported_categories": ["2-Day Shipping", "Next Day Air"],
            "comparisons": [
                {
                    "shipping_type": row.preference_value,
                    "recovered_percent": float(row.percent),
                    "recovered_rounded_1dp": round(float(row.percent), 1),
                    "matches_at_reported_precision": round(float(row.percent), 1) == 17.5,
                }
                for row in shipping.itertuples()
                if row.preference_value in ["2-Day Shipping", "Next Day Air"]
            ],
            "status": "Primary extension ages 18-27; the report's ages 13-28 are checked separately.",
            "age_18_27_shipping_percentages": dict(zip(shipping.preference_value, shipping.percent)),
        },
        "primary_comparison_age_range": "18-27",
        "exact_original_course_filter_recovered": False,
    }

    # Compare only the documented alternate definition, without trying other cutoffs.
    report_row = report_profile.iloc[0]
    report_shipping = report_preferences.loc[report_preferences.preference == "shipping"]
    course_comparisons["report_definition_replication"] = {
        "rationale": "Report page 5 defines Gen Z as born 1997-2012, ages 13-28. The shopping source starts at age 18.",
        "stated_report_age_range": "13-28 inclusive",
        "observed_data_age_range": "18-28 inclusive",
        "role": "Separate course replication diagnostic; the four primary age 18-27 versus 28-70 tests are unchanged.",
        "n": int(report_row.n),
        "review_rating": {
            "course_displayed": 3.79,
            "recovered_mean": float(report_row.mean_review_rating),
            "recovered_rounded_2dp": round(float(report_row.mean_review_rating), 2),
            "matches_at_reported_precision": round(float(report_row.mean_review_rating), 2) == 3.79,
        },
        "shipping_17_5_percent": [
            {
                "shipping_type": row.preference_value,
                "n": int(row.n),
                "course_displayed_percent": 17.5,
                "recovered_percent": float(row.percent),
                "recovered_rounded_1dp": round(float(row.percent), 1),
                "matches_at_reported_precision": round(float(row.percent), 1) == 17.5,
            }
            for row in report_shipping.itertuples()
            if row.preference_value in ["2-Day Shipping", "Next Day Air"]
        ],
        "all_preferences_file": "outputs/tables/shopping_report_definition_preferences.csv",
    }

    # Record provenance and limits next to the machine-readable numerical results.
    results = {
        "source": {
            "title": metadata["title"], "url": SOURCE_URL,
            "metadata_api_url": "https://www.kaggle.com/api/v1/datasets/view/iamsouravbanerjee/customer-shopping-trends-dataset",
            "pinned_download_url": DOWNLOAD_URL, "dataset_version": 2,
            "synthetic": True,
            "synthetic_disclosure": "The source describes data generated with ChatGPT for learning.",
            "license_label": metadata["licenseName"],
            "redistribution_status": "No clear raw-data redistribution grant was identified; raw data stay local.",
            "independent_of_financial_sample": True,
        },
        "input": {
            "file": args.input.name, "sha256": file_hash,
            "rows": len(raw), "columns": len(original_fields),
            "field_names": original_fields,
        },
        "quality": quality,
        "definitions": {
            "age_groups": {"18-27": "Age 18 through 27 inclusive", "28-70": "Age 28 through 70 inclusive"},
            "age_proxy_limit": "These are age groups, not verified generations; collection year is unknown.",
            "payment_input_field": payment_field,
            "payment_meaning": "Preferred payment. The updated file renames the full file's Preferred Payment Method field.",
            "frequency_mapping": frequency_mapping,
            "frequency_mapping_limit": "Bi-Weekly is interpreted as every two weeks, consistent with the source's Fortnightly label.",
            "prespecified_tests": preference_fields,
            "multiple_testing_method": "Holm across four tests", "alpha": 0.05,
        },
        "age_group_summary": profile.to_dict(orient="records"),
        "preference_tests": test_results,
        "age_18_27_shipping": shipping.to_dict(orient="records"),
        "age_18_27_frequency_normalized": frequency.to_dict(orient="records"),
        "age_18_27_frequency_original": raw_frequency.to_dict(orient="records"),
        "course_claim_comparisons": course_comparisons,
        "verification": {
            "sql_count_tables_independently_checked_with_pandas": preference_fields,
            "within_age_group_proportions_sum_to_one": True,
        },
        "limitations": [
            "Synthetic examples demonstrate a method and do not describe real Gen Z customers.",
            "The original course CSV variant and filtering code were not recovered; the report's stated age range is checked separately.",
            "The shopping and financial records have no verified common respondent key and are not joined.",
            "Statistical differences are associations within generated records, not marketing treatment effects.",
            "A non-significant result does not establish that the age groups have identical preferences.",
        ],
    }
    (output_dir / "shopping_results.json").write_text(
        json.dumps(results, indent=2, ensure_ascii=False, allow_nan=False) + "\n",
        encoding="utf-8",
    )

    # State the completed scope and the synthetic-data boundary clearly.
    significant = sum(item["significant_after_holm_0_05"] for item in test_results)
    print(f"Shopping analysis: {len(raw):,} synthetic records; age 18-27 n={int(young_profile.n)}.")
    print(f"Four planned tests completed; {significant} significant after Holm correction.")
    print("These results illustrate a method and are not evidence about real Gen Z consumers.")
    return 0


# Run the local analysis and preserve a nonzero exit status when data are unavailable.
if __name__ == "__main__":
    raise SystemExit(main())
