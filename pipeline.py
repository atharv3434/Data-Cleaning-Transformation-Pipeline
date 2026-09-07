"""Orchestrates the cleaning steps into a single pipeline, driven by config.yaml."""

import pandas as pd

import cleaning_steps as steps


def run_pipeline(df, config):
    """Run the full cleaning pipeline on a raw DataFrame.

    Returns (cleaned_df, report) where `report` is a dict summarizing every
    change made, suitable for saving as a JSON audit trail.
    """
    report = {"rows_in": len(df)}

    df = steps.standardize_column_names(df)

    df = steps.strip_and_case_text(
        df,
        columns=config.get("text_columns", []),
        case_map=config.get("text_case", {}),
        report=report,
    )

    df = steps.parse_dates(df, columns=config.get("date_columns", []), report=report)

    df = steps.coerce_numeric(df, columns=config.get("numeric_columns", []), report=report)

    quantity_min = config.get("quantity_min")
    if quantity_min is not None and "quantity" in df.columns:
        df = steps.enforce_minimum(df, "quantity", quantity_min, report)

    df = steps.handle_outliers_iqr(
        df,
        columns=config.get("outlier_columns", []),
        multiplier=config.get("iqr_multiplier", 1.5),
        action=config.get("outlier_action", "cap"),
        report=report,
    )

    df = steps.fill_missing(df, strategy=config.get("missing_value_strategy", {}), report=report)

    df = steps.drop_duplicates(df, subset=config.get("duplicate_subset", []), report=report)

    report["rows_out"] = len(df)
    report["rows_removed_total"] = report["rows_in"] - report["rows_out"]

    return df, report
