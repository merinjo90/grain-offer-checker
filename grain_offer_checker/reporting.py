"""Reporting: build review tables and export CSV and Excel files."""
import pandas as pd
from openpyxl.styles import Font, PatternFill
from openpyxl.utils import get_column_letter

STATUS_ERROR = "Error - not resolved"
STATUS_REVIEW = "Needs review"
STATUS_OK = "OK"

STATUS_COLOURS = {
    STATUS_ERROR: "F8CBAD",   # light red
    STATUS_REVIEW: "FFE699",  # light yellow
    STATUS_OK: "C6EFCE",      # light green
}


def build_reviewed_data(cleaned_df, issues_df):
    """Return the cleaned data with a status and issue summary for each record."""
    reviewed = cleaned_df.copy()
    statuses = []
    summaries = []
    for index in range(len(reviewed)):
        row_number = index + 1
        row_issues = issues_df[issues_df["row_number"] == row_number]
        summary = "; ".join(row_issues["field"] + ": " + row_issues["reason"])

        if (row_issues["severity"] == "error").any():
            statuses.append(STATUS_ERROR)
        elif (row_issues["severity"] == "review").any():
            statuses.append(STATUS_REVIEW)
        else:
            statuses.append(STATUS_OK)

        summaries.append(summary)

    reviewed.insert(0, "row_number", range(1, len(reviewed) + 1))
    reviewed.insert(1, "status", statuses)
    reviewed.insert(2, "issues", summaries)
    return reviewed


def build_summary(reviewed_df, issues_df, corrections):
    """Return the key numbers as a two-column table."""
    rows = [
        ("Records checked", len(reviewed_df)),
        ("Records OK", (reviewed_df["status"] == STATUS_OK).sum()),
        ("Records with unresolved errors", (reviewed_df["status"] == STATUS_ERROR).sum()),
        ("Records needing review", (reviewed_df["status"] == STATUS_REVIEW).sum()),
        ("Error issues", (issues_df["severity"] == "error").sum()),
        ("Review issues", (issues_df["severity"] == "review").sum()),
        ("Automatic corrections", len(corrections)),
        ("Note", "Synthetic demonstration data only"),
    ]
    return pd.DataFrame(rows, columns=["Metric", "Value"])


def build_offer_comparison(reviewed_df):
    """Compare price per capacity unit by equipment type, using OK records only."""
    ok = reviewed_df[reviewed_df["status"] == STATUS_OK].copy()
    ok["price_per_capacity_unit"] = (
        pd.to_numeric(ok["unit_price_eur"]) / pd.to_numeric(ok["capacity_t"])
    )
    comparison = (
        ok.groupby("equipment_type")["price_per_capacity_unit"]
        .agg(["count", "min", "mean", "max"])
        .round(2)
        .reset_index()
    )
    return comparison


def format_sheet(ws):
    """Bold headers, freeze the top row, add filters and fit column widths."""
    ws.freeze_panes = "A2"
    ws.auto_filter.ref = ws.dimensions
    for cell in ws[1]:
        cell.font = Font(bold=True)
    for column_cells in ws.columns:
        longest = max(len(str(cell.value)) if cell.value is not None else 0
                      for cell in column_cells)
        letter = get_column_letter(column_cells[0].column)
        ws.column_dimensions[letter].width = min(longest + 2, 60)


def colour_status(ws):
    """Colour the status column (B) of the Reviewed Data sheet."""
    for cell in ws["B"][1:]:
        colour = STATUS_COLOURS.get(cell.value)
        if colour:
            cell.fill = PatternFill(
                start_color=colour, end_color=colour, fill_type="solid"
            )


def export_issues_csv(issues_df, path):
    """Save the issues table as CSV."""
    issues_df.to_csv(path, index=False)


def export_excel(path, sheets):
    """Write each table to its own sheet. sheets = {sheet name: DataFrame}."""
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        for name, table in sheets.items():
            table.to_excel(writer, sheet_name=name, index=False)
            format_sheet(writer.sheets[name])
        colour_status(writer.sheets["Reviewed Data"])
