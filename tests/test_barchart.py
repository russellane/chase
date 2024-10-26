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
