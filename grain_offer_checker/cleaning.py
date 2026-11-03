"""Safe formatting corrections for synthetic offer data.

Only unambiguous formatting is corrected. The original DataFrame is never changed.
"""
import pandas as pd

TEXT_FIELDS = ["offer_id", "supplier", "equipment_type", "data_source"]
LOWERCASE_FIELDS = ["equipment_type", "data_source"]


def clean_value(field, value):
    """Return the safely cleaned version of one value."""
    cleaned = str(value).strip()
    if field in LOWERCASE_FIELDS:
        cleaned = cleaned.lower()
    return cleaned

def clean_data(df):
    """Return a cleaned copy of the data and a list of all corrections."""
    cleaned_df = df.copy()
    corrections = []
    for index, row in df.iterrows():
        for field in TEXT_FIELDS:
            original = row[field]
            if pd.isna(original):
                continue  # missing values are never filled in
            cleaned = clean_value(field, original)

            if cleaned != original:
                cleaned_df.at[index, field] = cleaned
                corrections.append({
                    "row_number": index + 1,
                    "offer_id": row["offer_id"],
                    "field": field,
                    "original_value": original,
                    "cleaned_value": cleaned,
                    "rule": "Removed extra spaces / standardised capitalisation",
                })

    return cleaned_df, corrections
