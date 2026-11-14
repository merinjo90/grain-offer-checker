"""Interactive review dashboard for the Grain Offer Checker.

Run from the project folder:

    streamlit run dashboard.py

It runs the same steps as the command-line pipeline (load -> clean -> validate)
and shows the results as charts and filterable tables. Nothing is written to disk.
"""
import io
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

from grain_offer_checker.cleaning import clean_data
from grain_offer_checker.pipeline import CORRECTION_COLUMNS, load_input
from grain_offer_checker.reporting import (
    STATUS_ERROR,
    STATUS_OK,
    STATUS_REVIEW,
    build_offer_comparison,
    build_reviewed_data,
    build_summary,
    export_excel,
)
from grain_offer_checker.validation import validate

PROJECT_DIR = Path(__file__).parent
SAMPLE_FILE = PROJECT_DIR / "data" / "raw" / "synthetic_offers.csv"
SAMPLE_FOLDER = PROJECT_DIR / "data" / "batch"

STATUS_ORDER = [STATUS_OK, STATUS_REVIEW, STATUS_ERROR]
STATUS_COLOURS = ["#2e9e5b", "#e0a800", "#d64545"]  # green, yellow, red
STATUS_SCALE = alt.Scale(domain=STATUS_ORDER, range=STATUS_COLOURS)


def check_name(reason):
    """Turn an issue's reason text into a short name for the rule that raised it."""
    if reason.startswith("Required"):
        return "Missing required value"
    if reason.startswith("Duplicate"):
        return "Duplicate offer ID"
    if reason.startswith(("Negative", "Must be at least", "Must be no more")):
        return "Number out of range"
    if reason.startswith("Must be a"):
        return "Not a valid number"
    if reason.startswith("Not a valid date"):
        return "Invalid date"
    if reason.startswith("Valid-until"):
        return "Expires before offer date"
    if reason.startswith("Not an allowed"):
        return "Value not allowed"
    if reason.startswith("Does not match"):
        return "Total ≠ quantity × unit price"
    if reason.startswith("AI-extracted"):
        return "AI-extracted (human check)"
    return "Other"


def run_checks(original):
    """Clean and validate one table. Returns every table the dashboard needs."""
    cleaned, corrections = clean_data(original)
    issues = validate(cleaned)
    reviewed = build_reviewed_data(cleaned, issues)
    corrections_df = pd.DataFrame(corrections, columns=CORRECTION_COLUMNS)
    summary = build_summary(reviewed, issues, corrections)
    comparison = build_offer_comparison(reviewed)
    return reviewed, issues, corrections_df, summary, comparison


def status_counts(reviewed, column):
    """Count offers per value of `column` and per status (for stacked bars)."""
    table = reviewed.copy()
    table[column] = table[column].fillna("(missing)")
    return table.groupby([column, "status"]).size().reset_index(name="offers")


def stacked_bar(counts, column, title):
    """Horizontal stacked bar chart of offer status per category."""
    return (
        alt.Chart(counts, title=title)
        .mark_bar()
        .encode(
            y=alt.Y(f"{column}:N", sort="-x", title=None, axis=alt.Axis(labelLimit=220)),
            x=alt.X("sum(offers):Q", title="Offers"),
            color=alt.Color("status:N", scale=STATUS_SCALE, title=None, sort=STATUS_ORDER,
                            legend=alt.Legend(orient="bottom")),
            order=alt.Order("status_rank:Q"),
            tooltip=[column, "status", "offers"],
        )
        .transform_calculate(
            status_rank=f"indexof({STATUS_ORDER!r}, datum.status)"
        )
        .properties(height=alt.Step(28))
    )


def for_display(table):
    """Show text columns as plain text.

    Columns that mix text and numbers (for example a unit price of "abc")
    cannot be shown directly by st.dataframe, so they are converted to text.
    """
    table = table.copy()
    for column in table.columns:
        if pd.api.types.is_object_dtype(table[column]):
            table[column] = table[column].fillna("").astype(str)
    return table


def excel_bytes(original, reviewed, issues, corrections_df, summary, comparison):
    """Build the same Excel report as the pipeline, in memory, for download."""
    buffer = io.BytesIO()
    export_excel(buffer, {
        "Summary": summary,
        "Reviewed Data": reviewed,
        "Issues": issues,
        "Corrections": corrections_df,
        "Offer Comparison": comparison,
        "Original Data": original,
    })
    return buffer.getvalue()


# ---------------------------------------------------------------- page layout
st.set_page_config(page_title="Grain Offer Checker", page_icon="🌾", layout="wide")
st.title("🌾 Grain Storage Offer Checker")
st.caption("Synthetic demonstration data only. Not real suppliers or prices.")

# --- Choose the data to check
with st.sidebar:
    st.header("Data")
    choice = st.radio(
        "What should be checked?",
        ["Sample file", "Sample batch folder", "Upload a CSV"],
    )
    uploaded = None
    if choice == "Upload a CSV":
        uploaded = st.file_uploader("CSV with the expected columns", type="csv")

if choice == "Sample file":
    original = load_input(SAMPLE_FILE)
elif choice == "Sample batch folder":
    original = load_input(SAMPLE_FOLDER)
elif uploaded is not None:
    original = pd.read_csv(uploaded)
    original.insert(0, "source_file", uploaded.name)
else:
    st.info("Upload a CSV file in the sidebar to check it.")
    st.stop()

try:
    reviewed, issues, corrections_df, summary, comparison = run_checks(original)
except KeyError as missing:
    st.error(f"The file is missing an expected column: {missing}")
    st.stop()

# --- Headline numbers
total = len(reviewed)
n_ok = int((reviewed["status"] == STATUS_OK).sum())
n_error = int((reviewed["status"] == STATUS_ERROR).sum())
n_review = int((reviewed["status"] == STATUS_REVIEW).sum())

st.markdown(
    f"**{n_ok} of {total}** offers ({n_ok / total:.0%}) passed every check. "
    f"**{n_error}** have errors a person must fix, and **{n_review}** need a human review."
)
cols = st.columns(5)
cols[0].metric("Records checked", total)
cols[1].metric("OK", n_ok)
cols[2].metric("Unresolved errors", n_error)
cols[3].metric("Needs review", n_review)
cols[4].metric("Automatic corrections", len(corrections_df))

# --- What was flagged, and where
left, right = st.columns(2)
with left:
    if issues.empty:
        st.success("No issues found.")
    else:
        by_check = issues.assign(check=issues["reason"].map(check_name))
        by_check = by_check.groupby(["check", "severity"]).size().reset_index(name="issues")
        chart = (
            alt.Chart(by_check, title="What the checker flagged")
            .mark_bar()
            .encode(
                y=alt.Y("check:N", sort="-x", title=None, axis=alt.Axis(labelLimit=220)),
                x=alt.X("issues:Q", title="Issues"),
                color=alt.Color("severity:N", title=None, legend=alt.Legend(orient="bottom"),
                                scale=alt.Scale(domain=["error", "review"],
                                                range=[STATUS_COLOURS[2], STATUS_COLOURS[1]])),
                tooltip=["check", "severity", "issues"],
            )
            .properties(height=alt.Step(28))
        )
        st.altair_chart(chart, width="stretch")
with right:
    st.altair_chart(
        stacked_bar(status_counts(reviewed, "equipment_type"), "equipment_type",
                    "Status by equipment type"),
        width="stretch",
    )

left, right = st.columns(2)
with left:
    st.altair_chart(
        stacked_bar(status_counts(reviewed, "supplier"), "supplier", "Status by supplier"),
        width="stretch",
    )
with right:
    st.altair_chart(
        stacked_bar(status_counts(reviewed, "data_source"), "data_source",
                    "Manual entry vs AI-extracted"),
        width="stretch",
    )

# --- Plausibility: capacity vs unit price
points = reviewed.assign(
    capacity=pd.to_numeric(reviewed["capacity_t"], errors="coerce"),
    unit_price=pd.to_numeric(reviewed["unit_price_eur"], errors="coerce"),
)
points = points[(points["capacity"] > 0) & (points["unit_price"] > 0)]
scatter = (
    alt.Chart(for_display(points), title="Capacity vs unit price (log scales) — outliers stand out")
    .mark_circle(size=90, opacity=0.85)
    .encode(
        x=alt.X("capacity:Q", scale=alt.Scale(type="log"),
                title="Capacity (t for silos, t/h for others)"),
        y=alt.Y("unit_price:Q", scale=alt.Scale(type="log"), title="Unit price (€)"),
        color=alt.Color("status:N", scale=STATUS_SCALE, title="Status", sort=STATUS_ORDER),
        tooltip=["offer_id", "supplier", "equipment_type", "capacity", "unit_price",
                 "status", "issues"],
    )
    .properties(height=380)
)
st.altair_chart(scatter, width="stretch")

# --- Price per capacity unit (OK offers only)
st.subheader("Price per capacity unit (OK offers only)")
st.caption("Unit price ÷ capacity. Silos are € per tonne, the others € per tonne/hour, "
           "so compare only within the same equipment type.")
left, right = st.columns([3, 2])
ok = reviewed[reviewed["status"] == STATUS_OK].copy()
if ok.empty:
    left.info("No OK offers to compare.")
else:
    ok["price_per_capacity_unit"] = (
        pd.to_numeric(ok["unit_price_eur"]) / pd.to_numeric(ok["capacity_t"])
    )
    strip = (
        alt.Chart(for_display(ok))
        .mark_tick(thickness=3, size=22)
        .encode(
            x=alt.X("price_per_capacity_unit:Q", scale=alt.Scale(type="log"),
                    title="€ per capacity unit (log scale)"),
            y=alt.Y("equipment_type:N", title=None),
            color=alt.value(STATUS_COLOURS[0]),
            tooltip=["offer_id", "supplier", alt.Tooltip("price_per_capacity_unit:Q", format=",.2f")],
        )
        .properties(height=alt.Step(40))
    )
    left.altair_chart(strip, width="stretch")
right.dataframe(for_display(comparison), hide_index=True, width="stretch")

# --- All records, filterable
st.subheader("All reviewed offers")
left, right = st.columns([1, 2])
picked = left.multiselect("Status", STATUS_ORDER, default=STATUS_ORDER)
search = right.text_input("Search offer ID, supplier or type")
shown = reviewed[reviewed["status"].isin(picked)]
if search:
    text = shown[["offer_id", "supplier", "equipment_type"]].astype(str)
    mask = text.apply(lambda col: col.str.contains(search, case=False)).any(axis=1)
    shown = shown[mask]
st.caption(f"Showing {len(shown)} of {total} offers")


def colour_status(value):
    colours = dict(zip(STATUS_ORDER, ["#c6efce", "#ffe699", "#f8cbad"]))
    return f"background-color: {colours.get(value, '')}"


st.dataframe(
    for_display(shown).style.map(colour_status, subset=["status"]),
    hide_index=True,
    width="stretch",
)

left, right = st.columns(2)
with left:
    st.subheader("Issues")
    st.dataframe(for_display(issues), hide_index=True, width="stretch")
with right:
    st.subheader("Automatic corrections")
    st.dataframe(for_display(corrections_df), hide_index=True, width="stretch")

# --- Downloads
st.download_button(
    "Download Excel report",
    data=excel_bytes(original, reviewed, issues, corrections_df, summary, comparison),
    file_name="review_report.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
)
