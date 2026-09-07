# Data Cleaning & Transformation Pipeline

A configurable pipeline for cleaning messy tabular data, built on **numpy**
and **pandas**. Ships with an intentionally messy sample sales dataset —
duplicates, missing values, inconsistent date formats, mixed-type columns,
whitespace/casing issues, and outliers — so you can see every step in
action immediately, then point it at your own data.

## Project structure

```
data-cleaning-pipeline/
├── config.yaml                    # all cleaning rules live here
├── requirements.txt
├── data/
│   ├── raw/
│   │   └── messy_sales_data.csv   # sample messy input
│   └── processed/                 # cleaned output + report land here
├── src/
│   ├── utils.py                   # config loading, column name helpers
│   ├── cleaning_steps.py          # individual, composable cleaning functions
│   ├── pipeline.py                # orchestrates the steps in order
│   └── run_pipeline.py            # CLI entry point
└── README.md
```

## Setup

```bash
pip install -r requirements.txt
```

## Run it

```bash
python src/run_pipeline.py
```

This reads `data/raw/messy_sales_data.csv`, runs it through every cleaning
step defined in `config.yaml`, and writes:

- `data/processed/cleaned_sales_data.csv` — the cleaned data
- `data/processed/cleaning_report.json` — an audit trail of exactly what
  was fixed (counts of duplicates removed, values normalized, missing
  values filled, outliers capped, etc.)

A summary also prints to the console, e.g.:

```
Rows in:  30
Rows out: 25
Duplicate rows removed: 3
Text values normalized: 15
Missing values handled per column:
  amount: 4
  quantity: 4
  email: 2
  order_date: 2
Outliers handled per column:
  amount: 2 values capped (bounds: -195.46 to 503.26)
```

## What it cleans

| Problem in the raw data | How it's fixed |
|---|---|
| Inconsistent column names (`"Order ID"`) | Standardized to snake_case (`order_id`) |
| Leading/trailing whitespace, inconsistent casing (`"  john smith"`, `"JANE DOE"`) | Stripped and title-cased |
| Multiple date formats (`2024-01-15`, `01/16/2024`, `16-Jan-2024`) | Parsed into a single consistent date type; unparseable values are counted, not silently dropped |
| Non-numeric junk in numeric columns (`"five"`, `"N/A"`) | Coerced to numeric; invalid values become missing and are counted |
| Invalid values (negative/zero quantity) | Treated as missing before filling |
| Missing values | Filled per-column using the strategy in `config.yaml` (median, a literal value, or drop the row) |
| Exact duplicate transactions (re-entered under a new ID) | Removed based on a configurable set of key columns |
| Extreme outliers (e.g. a `999999.00` sale) | Detected with the IQR method (via `numpy.percentile`) and capped to a reasonable bound |

## Configuring it for your own data

Everything is driven by `config.yaml` — no code changes needed for most
adjustments:

- `input_path` / `output_path` / `report_path` — file locations
- `text_columns` / `text_case` — which columns to strip/normalize and how
- `date_columns` — which columns to parse as dates
- `numeric_columns` — which columns to coerce to numbers
- `missing_value_strategy` — per-column: `"drop_row"`, `"median"`, `"mean"`,
  or a literal fill value (e.g. `"Unknown"`)
- `duplicate_subset` — which columns define a "duplicate" row
- `outlier_columns` / `iqr_multiplier` / `outlier_action` — outlier
  detection sensitivity and whether to `cap` or `remove` them

Point `input_path` at your own CSV, adjust the column lists to match your
schema, and re-run.

## Extending this project

- **New cleaning step**: add a function to `cleaning_steps.py` (following
  the same `(df, ..., report) -> df` pattern) and call it from
  `pipeline.run_pipeline()`.
- **Other outlier methods**: `cleaning_steps.handle_outliers_iqr` is the
  place to add a z-score or percentile-clip alternative.
- **Multiple input files**: `run_pipeline.py` can be adapted to loop over a
  directory of raw files and clean each one with the same rules.
