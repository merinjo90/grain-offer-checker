"""Tests for the validation rules, using small hand-made examples."""
import pandas as pd

from grain_offer_checker.validation import (
    check_required_fields,
    check_duplicate_ids,
    check_numbers,
    check_dates,
    check_ai_extracted,
    validate,
)


def make_offer(**changes):
    """Create a valid offer, then apply the requested changes."""
    offer = {
        "offer_id": "OFF-001",
        "supplier": "Synthetic Supplier A",
        "equipment_type": "silo",
        "capacity_t": 5000,
        "quantity": 2,
        "unit_price_eur": 150000,
        "total_price_eur": 300000,
        "offer_date": "2026-03-10",
        "valid_until": "2026-06-10",
        "delivery_weeks": 12,
        "data_source": "manual_entry",
    }
    offer.update(changes)
    return offer


def make_df(*offers):
    """Build a table from one or more offer dictionaries."""
    return pd.DataFrame(list(offers))


def test_valid_offer_has_no_issues():
    assert len(validate(make_df(make_offer()))) == 0


def test_missing_supplier_is_reported():
    issues = check_required_fields(make_df(make_offer(supplier="")))
    assert len(issues) == 1
    assert issues[0]["field"] == "supplier"
    assert issues[0]["severity"] == "error"


def test_both_duplicate_ids_are_reported():
    df = make_df(make_offer(), make_offer(supplier="Synthetic Supplier B"))
    issues = check_duplicate_ids(df)
    assert len(issues) == 2
    assert {issue["row_number"] for issue in issues} == {1, 2}


def test_negative_quantity_is_reported():
    issues = check_numbers(make_df(make_offer(quantity=-2)))
    assert any(
        issue["field"] == "quantity" and issue["reason"] == "Negative value"
        for issue in issues
    )


def test_decimal_quantity_is_rejected():
    issues = check_numbers(make_df(make_offer(quantity=2.5)))
    assert len(issues) == 1
    assert issues[0]["field"] == "quantity"
    assert issues[0]["reason"] == "Must be a whole number"


def test_invalid_date_skips_order_comparison():
    issues = check_dates(make_df(make_offer(offer_date="2026-02-30")))
    assert len(issues) == 1
    assert issues[0]["field"] == "offer_date"
    assert "Not a valid date" in issues[0]["reason"]


def test_expiry_before_offer_date_is_reported():
    issues = check_dates(make_df(make_offer(valid_until="2026-03-01")))
    assert len(issues) == 1
    assert issues[0]["field"] == "valid_until"
    assert issues[0]["reason"] == "Valid-until date is before offer date"


def test_ai_extracted_record_needs_review():
    issues = check_ai_extracted(make_df(make_offer(data_source="ai_extracted")))
    assert len(issues) == 1
    assert issues[0]["field"] == "data_source"
    assert issues[0]["severity"] == "review"
