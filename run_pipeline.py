"""Run the data cleaning pipeline end to end.

Usage:
    python src/run_pipeline.py [--config config.yaml]

Loads the raw CSV, applies every cleaning step defined in config.yaml, then
saves the cleaned CSV and a JSON report summarizing exactly what was fixed.

"""

import argparse
import json
import os
import sys

import pandas as pd

sys.path.append(os.path.dirname(__file__))
from utils import load_config
from pipeline import run_pipeline


def main():
    parser = argparse.ArgumentParser(description="Run the data cleaning pipeline.")
    parser.add_argument("--config", default="config.yaml", help="Path to config.yaml")
    args = parser.parse_args()

    config = load_config(args.config)

    input_path = config["input_path"]
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Could not find input data at '{input_path}'")

    print(f"Reading raw data from {input_path} ...")
    raw_df = pd.read_csv(input_path)
    print(f"Loaded {len(raw_df)} rows, {len(raw_df.columns)} columns.")

    print("Running cleaning pipeline...")
    cleaned_df, report = run_pipeline(raw_df, config)

    output_path = config["output_path"]
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    cleaned_df.to_csv(output_path, index=False)

    report_path = config["report_path"]
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, default=str)

    print(f"\nCleaned data saved to {output_path}")
    print(f"Cleaning report saved to {report_path}\n")

    print("Summary:")
    print(f"  Rows in:  {report['rows_in']}")
    print(f"  Rows out: {report['rows_out']}")
    print(f"  Duplicate rows removed: {report.get('duplicate_rows_removed', 0)}")
    print(f"  Text values normalized: {report.get('text_values_normalized', 0)}")
    if report.get("missing_values_handled"):
        print("  Missing values handled per column:")
        for col, count in report["missing_values_handled"].items():
            print(f"    {col}: {count}")
    if report.get("outliers_handled"):
        print("  Outliers handled per column:")
        for col, info in report["outliers_handled"].items():
            print(f"    {col}: {info['count']} values {info['action']}ped "
                  f"(bounds: {info['lower_bound']} to {info['upper_bound']})")


if __name__ == "__main__":
    main()
