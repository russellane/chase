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
