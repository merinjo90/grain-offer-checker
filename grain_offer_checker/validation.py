"""Validation rules for synthetic equipment offer data.

Each check returns a list of issues. Each issue is a dictionary.
"""
import pandas as pd

REQUIRED_FIELDS = [
    "offer_id", "supplier", "equipment_type", "capacity_t", "quantity",
    "unit_price_eur", "total_price_eur", "offer_date", "valid_until",
    "data_source",
]


def make_issue(index, row, field, reason, severity="error"):
    """Create one issue as a dictionary."""
    return {
        "row_number": index + 1,
        "offer_id": row["offer_id"],
        "field": field,
        "original_value": row[field],
        "reason": reason,
        "severity": severity,
    }


def is_missing(value):
    """Return True if a value is empty, NaN or only spaces."""
    if pd.isna(value):
        return True
    return str(value).strip() == ""


def check_required_fields(df):
    """Flag required fields that are empty."""
    issues = []
    for index, row in df.iterrows():
        for field in REQUIRED_FIELDS:
            if is_missing(row[field]):
                issues.append(make_issue(index, row, field, "Required field is missing"))
    return issues

def check_duplicate_ids(df):
    """Flag every row with a repeated offer ID."""
    issues = []
    duplicated = df["offer_id"].duplicated(keep=False)
    for index, row in df.iterrows():
        if duplicated[index]:
            issues.append(make_issue(index, row, "offer_id", "Duplicate offer ID"))
    return issues
