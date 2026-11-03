"""Run the full check: load -> clean -> validate -> build tables -> export."""
import argparse
from pathlib import Path

import pandas as pd

from grain_offer_checker.cleaning import clean_data
from grain_offer_checker.validation import validate
from grain_offer_checker.reporting import (
    build_reviewed_data,
    build_summary,
    build_offer_comparison,
    export_issues_csv,
    export_excel,
)

CORRECTION_COLUMNS = [
    "row_number", "offer_id", "field", "original_value", "cleaned_value", "rule",
]


def load_input(input_path):
    """Load one CSV file, or every CSV file in a folder, into one table."""
    input_path = Path(input_path)
    if input_path.is_dir():
        files = sorted(input_path.glob("*.csv"))
        if not files:
            raise SystemExit(f"No CSV files found in {input_path}")
    else:
        files = [input_path]

    tables = []
    for file in files:
        table = pd.read_csv(file)
        table.insert(0, "source_file", file.name)
        tables.append(table)

    return pd.concat(tables, ignore_index=True)


def run(input_path, output_dir):
    """Check one CSV file or a folder of CSV files and write the reports."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    original = load_input(input_path)
    cleaned, corrections = clean_data(original)
    issues = validate(cleaned)
    issues.insert(1, "source_file",
                  [cleaned.loc[n - 1, "source_file"] for n in issues["row_number"]])
    reviewed = build_reviewed_data(cleaned, issues)
    corrections_df = pd.DataFrame(corrections, columns=CORRECTION_COLUMNS)

    summary = build_summary(reviewed, issues, corrections)

    export_issues_csv(issues, output_dir / "issues_report.csv")

    export_excel(output_dir / "review_report.xlsx", {
        "Summary": summary,
        "Reviewed Data": reviewed,
        "Issues": issues,
        "Corrections": corrections_df,
        "Offer Comparison": build_offer_comparison(reviewed),
        "Original Data": original,
    })

    return summary


def main():
    parser = argparse.ArgumentParser(description="Check synthetic equipment offer data.")
    parser.add_argument(
        "--input",
        default="data/raw/synthetic_offers.csv",
        help="CSV file or folder containing CSV files",
    )
    parser.add_argument("--output", default="output",
                        help="folder for the reports")
    args = parser.parse_args()

    summary = run(args.input, args.output)
    print(summary.to_string(index=False))
    print(f"\nReports written to: {args.output}/")


if __name__ == "__main__":
    main()
