"""End-to-end test: the full pipeline on the synthetic data matches the answer key."""
from grain_offer_checker.pipeline import run


def test_pipeline_matches_answer_key(tmp_path):
    summary = run("data/raw/synthetic_offers.csv", tmp_path)
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
