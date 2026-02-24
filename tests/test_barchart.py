import sys

import pytest
from pytest_mock.plugin import MockerFixture

from chase.cli import ChaseCLI


@pytest.fixture(name="matplotlib")
def _matplotlib(mocker: MockerFixture) -> None:
    mocker.patch("matplotlib.pyplot.show")


def run(options: list[str]) -> None:
    sys.argv = ["chase"]
    if options:
        sys.argv += options
    sys.argv += ["--barchart", "-s", "foy", "-e", "fom", "--use-datafiles"]
    print(f"Running {sys.argv!r}")
    ChaseCLI().main()


def test_barchart(matplotlib: str) -> None:
    _ = matplotlib  # unused-argument
    run([])


def test_barchart_no_exclude(matplotlib: str) -> None:
    _ = matplotlib  # unused-argument
    run(["--no-exclude-chart-categories"])


def test_barchart_averages_only(matplotlib: str) -> None:
    _ = matplotlib  # unused-argument
    run(["--averages-only"])


def test_barchart_monthly_averages_only(matplotlib: str) -> None:
    _ = matplotlib  # unused-argument
    run(["--monthly", "--moving-average"])


def test_barchart_monthly_groceries(matplotlib: str) -> None:
    _ = matplotlib  # unused-argument
    run(["--monthly", "--category", "Groceries"])


def test_barchart_category_totals_no_date_filter(matplotlib: str) -> None:
    """Test barchart category totals without date filter to cover _get_category_totals."""
    _ = matplotlib  # unused-argument
    sys.argv = ["chase", "--barchart", "--use-datafiles", "--no-exclude-chart-categories"]
    print(f"Running {sys.argv!r}")
    ChaseCLI().main()


def test_barchart_with_exclusions(matplotlib: str) -> None:
    """Test barchart with category exclusions to cover the continue branch."""
    _ = matplotlib  # unused-argument
    sys.argv = ["chase", "--barchart", "--use-datafiles"]
    print(f"Running {sys.argv!r}")
    ChaseCLI().main()


def test_barchart_averages_no_date_filter(matplotlib: str) -> None:
    """Test barchart averages without date filter to cover _get_monthly_averages loop."""
    _ = matplotlib  # unused-argument
    sys.argv = ["chase", "--barchart", "--use-datafiles", "--averages-only"]
    print(f"Running {sys.argv!r}")
    ChaseCLI().main()


def test_barchart_monthly_category_no_date_filter(matplotlib: str) -> None:
    """Test barchart monthly category without date filter to cover _get_monthly_totals."""
    _ = matplotlib  # unused-argument
    sys.argv = ["chase", "--barchart", "--use-datafiles", "--category", "Groceries"]
    print(f"Running {sys.argv!r}")
    ChaseCLI().main()
