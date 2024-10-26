import subprocess
import sys

from chase.cli import ChaseCLI


def run_shell(options: list[str]) -> None:
    """Test running from the shell."""

    argv = ["python", "-m", "chase"]
    if options:
        argv += options
    print(f"\nRunning {argv!r}", flush=True)
    subprocess.run(argv, check=True)


def test_run_shell() -> None:
    run_shell(["--use-datafiles", "-s", "foy", "-e", "fom", "--use-datafiles"])


def run_cli(options: list[str]) -> None:
    """Test calling the cli directly."""

    sys.argv = ["chase"]
    if options:
        sys.argv += options
    print(f"\nRunning {sys.argv!r}", flush=True)
    ChaseCLI().main()


def test_file_dev_null() -> None:
    run_cli(["/dev/null"])


def test_use_datafiles_no_dates() -> None:
    run_cli(["--use-datafiles"])


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
