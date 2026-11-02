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

# Plausible ranges: (minimum, maximum). None = no maximum.
NUMERIC_RULES = {
    "capacity_t": (1, 20000),
    "quantity": (1, None),
    "unit_price_eur": (1, None),
    "total_price_eur": (1, None),
    "delivery_weeks": (1, 52),
}


def to_number(value):
    """Convert a value to a number. Return None if that is not possible."""
    if is_missing(value):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def check_numbers(df):
    """Flag invalid, negative, non-whole and out-of-range numbers."""
    issues = []
    for index, row in df.iterrows():
        for field, (minimum, maximum) in NUMERIC_RULES.items():
            value = row[field]
            if is_missing(value):
                continue  # missing values are handled by check_required_fields
            number = to_number(value)

            if number is None:
                issues.append(
                    make_issue(index, row, field, "Must be a number")
                )
                continue

            if number < 0:
                issues.append(
                    make_issue(index, row, field, "Negative value")
                )
                continue

            if field in ("quantity", "delivery_weeks"):
                if not number.is_integer():
                    issues.append(
                        make_issue(index, row, field, "Must be a whole number")
                    )
                    continue

            if number < minimum:
                issues.append(
                    make_issue(
                        index, row, field,
                        f"Must be at least {minimum}"
                    )
                )
            elif maximum is not None and number > maximum:
                issues.append(
                    make_issue(
                        index, row, field,
                        f"Must be no more than {maximum}"
                    )
                )

    return issues

DATE_FIELDS = ["offer_date", "valid_until"]


def to_date(value):
    """Convert YYYY-MM-DD text to a date. Return None if that is not possible."""
    if is_missing(value):
        return None
    result = pd.to_datetime(str(value).strip(), format="%Y-%m-%d", errors="coerce")
    if pd.isna(result):
        return None
    return result
def check_dates(df):
    """Flag invalid dates and offers that expire before they start."""
    issues = []
    for index, row in df.iterrows():
        for field in DATE_FIELDS:
            value = row[field]
            if not is_missing(value) and to_date(value) is None:
                issues.append(
                    make_issue(index, row, field, "Not a valid date (expected YYYY-MM-DD)")
                )

        offer_date = to_date(row["offer_date"])
        valid_until = to_date(row["valid_until"])

        if offer_date is not None and valid_until is not None and valid_until < offer_date:
            issues.append(
                make_issue(index, row, "valid_until", "Valid-until date is before offer date")
            )

    return issues
