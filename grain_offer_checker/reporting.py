"""Reporting: build review tables and export CSV and Excel files."""
import pandas as pd

STATUS_ERROR = "Error - not resolved"
STATUS_REVIEW = "Needs review"
STATUS_OK = "OK"


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
