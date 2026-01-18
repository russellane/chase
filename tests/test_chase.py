import sys

import pytest

from chase.cli import main


def run_cli(options: list[str]) -> None:
    """Test calling the cli directly."""

    sys.argv = ["chase"]
    if options:
        sys.argv += options
    print(f"\nRunning {sys.argv!r}", flush=True)
    main()


def test_print_sample_config() -> None:
    with pytest.raises(SystemExit) as err:
        run_cli(["--print-sample-config"])
    assert err.value.code == 0


def test_file_dev_null() -> None:
    run_cli(["/dev/null"])


def test_use_datafiles_no_dates() -> None:
    run_cli(["--use-datafiles"])


def test_use_datafiles_no_dates_category() -> None:
    run_cli(["--use-datafiles", "--category", "Groceries"])


def test_use_datafiles_no_dates_no_color() -> None:
    run_cli(["--use-datafiles", "--no-color"])


def test_dates() -> None:
    run_cli(["--use-datafiles", "-s", "2024-01-01", "-e", "2024-10-01"])


def test_report() -> None:
    run_cli(["--use-datafiles", "-s", "foy", "-e", "fom"])


def test_report_detail() -> None:
    run_cli(["--use-datafiles", "-s", "foy", "-e", "fom", "--detail"])


def test_monthly() -> None:
    run_cli(["--use-datafiles", "-s", "foy", "-e", "fom", "--monthly"])


def test_monthly_detail() -> None:
    run_cli(["--use-datafiles", "-s", "foy", "-e", "fom", "--monthly", "--detail"])


def test_monthly_averages_only() -> None:
    run_cli(["--use-datafiles", "-s", "foy", "-e", "fom", "--monthly", "--averages-only"])


def test_monthly_averages_only_groceries() -> None:
    run_cli(
        [
            "--use-datafiles",
            "-s",
            "foy",
            "-e",
            "fom",
            "--monthly",
            "--averages-only",
            "--category",
            "Groceries",
        ]
    )


def test_monthly_no_date_filter() -> None:
    """Test monthly report without date filtering to ensure loop body is covered."""
    run_cli(["--use-datafiles", "--monthly"])


def test_monthly_detail_no_date_filter() -> None:
    """Test monthly detail report to cover _print_monthly_report_merchants."""
    run_cli(["--use-datafiles", "--monthly", "--detail"])


def test_report_detail_no_date_filter() -> None:
    """Test report detail without date filter to cover transaction printing."""
    run_cli(["--use-datafiles", "--detail"])


def test_monthly_with_category_filter() -> None:
    """Test monthly report with category filter to cover the continue branch."""
    run_cli(["--use-datafiles", "--monthly", "--category", "Groceries"])
