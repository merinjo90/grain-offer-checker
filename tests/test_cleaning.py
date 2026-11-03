"""Tests for safe formatting corrections."""
import pandas as pd

from grain_offer_checker.cleaning import clean_data


def make_df(**changes):
    """Create a one-row table with the text fields that cleaning handles."""
    row = {
        "offer_id": "OFF-001",
        "supplier": "Synthetic Supplier A",
        "equipment_type": "silo",
        "data_source": "manual_entry",
    }
    row.update(changes)
    return pd.DataFrame([row])


def test_spaces_and_capitals_are_fixed():
    df = make_df(supplier="  Synthetic Supplier A ", equipment_type=" Silo ")
    cleaned, corrections = clean_data(df)
    assert cleaned.loc[0, "equipment_type"] == "silo"
    assert cleaned.loc[0, "supplier"] == "Synthetic Supplier A"
    assert len(corrections) == 2


def test_missing_value_is_not_filled():
    df = make_df(supplier=None)
    cleaned, corrections = clean_data(df)
    assert pd.isna(cleaned.loc[0, "supplier"])
    assert corrections == []


def test_clean_data_makes_no_corrections():
    cleaned, corrections = clean_data(make_df())
    assert corrections == []


def test_original_data_is_not_changed():
    df = make_df(equipment_type=" Silo ")
    clean_data(df)
    assert df.loc[0, "equipment_type"] == " Silo "
