"""End-to-end tests for the full pipeline."""
import pandas as pd

from grain_offer_checker.pipeline import run

SYNTHETIC = "data/raw/synthetic_offers.csv"


def test_pipeline_matches_answer_key(tmp_path):
    summary = run(SYNTHETIC, tmp_path)
    values = dict(zip(summary["Metric"], summary["Value"]))

    assert values["Records checked"] == 45
    assert values["Records OK"] == 29
    assert values["Records with unresolved errors"] == 11
    assert values["Records needing review"] == 5
    assert values["Error issues"] == 12
    assert values["Review issues"] == 7
    assert values["Automatic corrections"] == 2

    assert (tmp_path / "review_report.xlsx").exists()
    assert (tmp_path / "issues_report.csv").exists()


def test_folder_input_matches_single_file(tmp_path):
    folder = tmp_path / "batch"
    folder.mkdir()
    df = pd.read_csv(SYNTHETIC)
    df.iloc[:20].to_csv(folder / "week1.csv", index=False)
    df.iloc[20:].to_csv(folder / "week2.csv", index=False)

    single = run(SYNTHETIC, tmp_path / "single_out")
    combined = run(folder, tmp_path / "combined_out")

    assert list(single["Value"]) == list(combined["Value"])


def test_same_id_in_two_files_is_a_duplicate(tmp_path):
    folder = tmp_path / "batch"
    folder.mkdir()
    first_offer = pd.read_csv(SYNTHETIC).iloc[[0]]
    first_offer.to_csv(folder / "a.csv", index=False)
    first_offer.to_csv(folder / "b.csv", index=False)

    run(folder, tmp_path / "out")
    issues = pd.read_csv(tmp_path / "out" / "issues_report.csv")
    duplicates = issues[issues["reason"] == "Duplicate offer ID"]

    assert len(duplicates) == 2
    assert set(duplicates["source_file"]) == {"a.csv", "b.csv"}
