"""Individual, composable cleaning steps.

Each function takes a DataFrame (and sometimes a shared `report` dict to
record what it changed) and returns the transformed DataFrame. Keeping each
step small and single-purpose makes the pipeline easy to reorder, test, or
extend with new steps.
"""

import numpy as np
import pandas as pd

from utils import to_snake_case


def standardize_column_names(df):
    """Rename columns to consistent snake_case, e.g. 'Order ID' -> 'order_id'."""
    df = df.rename(columns={c: to_snake_case(c) for c in df.columns})
    return df


def strip_and_case_text(df, columns, case_map, report):
    """Strip surrounding whitespace and normalize casing on text columns.

    This fixes issues like '  John Smith' / 'JOHN SMITH' / 'john smith' all
    referring to the same person, and 'North' / 'north ' / 'NORTH' all
    referring to the same region.
    """
    changed = 0
    for col in columns:
        if col not in df.columns:
            continue
        original = df[col].copy()
        stripped = df[col].astype("string").str.strip()

        case = case_map.get(col, "title")
        if case == "title":
            stripped = stripped.str.title()
        elif case == "upper":
            stripped = stripped.str.upper()
        elif case == "lower":
            stripped = stripped.str.lower()

        df[col] = stripped
        changed += int((original.astype("string") != df[col]).sum())

    report["text_values_normalized"] = report.get("text_values_normalized", 0) + changed
    return df


def parse_dates(df, columns, report):
    """Parse date columns that may arrive in several different formats.

    Values that can't be parsed at all become NaT (missing) rather than
    raising an error, and the count of unparseable values is recorded so
    it's visible in the cleaning report.
    """
    for col in columns:
        if col not in df.columns:
            continue
        before_missing = df[col].isna().sum()
        parsed = pd.to_datetime(df[col], errors="coerce", format="mixed")
        after_missing = parsed.isna().sum()
        newly_unparseable = after_missing - before_missing
        report.setdefault("unparseable_dates", {})[col] = int(newly_unparseable)
        df[col] = parsed
    return df


def coerce_numeric(df, columns, report):
    """Force columns to numeric, turning non-numeric junk (e.g. 'five', 'N/A')
    into missing values rather than leaving mixed types in the column.
    """
    for col in columns:
        if col not in df.columns:
            continue
        before_missing = df[col].isna().sum()
        numeric = pd.to_numeric(df[col], errors="coerce")
        after_missing = numeric.isna().sum()
        newly_invalid = after_missing - before_missing
        report.setdefault("non_numeric_values_coerced", {})[col] = int(newly_invalid)
        df[col] = numeric
    return df


def enforce_minimum(df, column, minimum, report):
    """Treat values below a minimum (e.g. a negative or zero quantity) as
    missing, since they represent a data-entry error rather than a real
    reading. Uses numpy's vectorized comparison rather than a Python loop.
    """
    if column not in df.columns:
        return df
    values = df[column].to_numpy(dtype="float64", na_value=np.nan)
    invalid_mask = values < minimum
    count = int(np.nansum(invalid_mask))
    df.loc[invalid_mask, column] = np.nan
    report.setdefault("below_minimum_treated_as_missing", {})[column] = count
    return df


def handle_outliers_iqr(df, columns, multiplier, action, report):
    """Detect outliers with the IQR (interquartile range) method using numpy,
    then either cap them to the bounds or remove those rows entirely.
    """
    for col in columns:
        if col not in df.columns:
            continue
        values = df[col].to_numpy(dtype="float64")
        finite = values[~np.isnan(values)]
        if finite.size == 0:
            continue

        q1, q3 = np.percentile(finite, [25, 75])
        iqr = q3 - q1
        lower = q1 - multiplier * iqr
        upper = q3 + multiplier * iqr

        outlier_mask = (values < lower) | (values > upper)
        outlier_mask = outlier_mask & ~np.isnan(values)
        count = int(outlier_mask.sum())

        if action == "cap":
            capped = np.clip(values, lower, upper)
            df[col] = capped
        elif action == "remove":
            df = df.loc[~outlier_mask].reset_index(drop=True)

        report.setdefault("outliers_handled", {})[col] = {
            "count": count,
            "action": action,
            "lower_bound": round(float(lower), 2),
            "upper_bound": round(float(upper), 2),
        }
    return df


def fill_missing(df, strategy, report):
    """Apply a per-column missing-value strategy.

    "drop_row" removes rows missing that column; "median"/"mean" fill with
    the column's median/mean; anything else is used as a literal fill value.
    """
    filled_counts = {}
    for col, rule in strategy.items():
        if col not in df.columns:
            continue
        missing_before = int(df[col].isna().sum())
        if missing_before == 0:
            continue

        if rule == "drop_row":
            df = df.dropna(subset=[col]).reset_index(drop=True)
        elif rule == "median":
            df[col] = df[col].fillna(df[col].median())
        elif rule == "mean":
            df[col] = df[col].fillna(df[col].mean())
        else:
            df[col] = df[col].fillna(rule)

        filled_counts[col] = missing_before

    report["missing_values_handled"] = filled_counts
    return df


def drop_duplicates(df, subset, report):
    """Remove exact duplicate rows based on a subset of key columns."""
    subset = [c for c in subset if c in df.columns]
    before = len(df)
    df = df.drop_duplicates(subset=subset, keep="first").reset_index(drop=True)
    report["duplicate_rows_removed"] = before - len(df)
    return df
