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
    sys.argv += ["--piechart", "-s", "foy", "-e", "fom", "--use-datafiles"]
    print(f"Running {sys.argv!r}")
    ChaseCLI().main()


def test_piechart(matplotlib: str) -> None:
    _ = matplotlib  # unused-argument
    run([])


def test_piechart_no_exclude(matplotlib: str) -> None:
    _ = matplotlib  # unused-argument
    run(["--no-exclude-chart-categories"])


def test_piechart_averages_only(matplotlib: str) -> None:
    _ = matplotlib  # unused-argument
    run(["--averages-only"])


def test_piechart_monthly_averages_only(matplotlib: str) -> None:
    _ = matplotlib  # unused-argument
    run(["--monthly", "--moving-average"])


def test_piechart_monthly_groceries(matplotlib: str) -> None:
    _ = matplotlib  # unused-argument
    run(["--monthly", "--category", "Groceries"])
