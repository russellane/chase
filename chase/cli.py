"""Command line interface."""

from glob import glob
from pathlib import Path
from time import localtime, mktime, strftime, strptime

from libcli import BaseCLI

from chase.chase import Chase

__all__ = ["ChaseCLI"]


class ChaseCLI(BaseCLI):
    """Command line-interface."""

    config = {
        "config-file": "~/.chase.toml",
    }

    def init_parser(self) -> None:
        """Initialize argument parser."""

        self.ArgumentParser(
            prog=__package__,
            description="Process Chase Bank transaction files.",
            epilog=self.dedent(
                """
        For example,

        Print each Category, in descending order of the total spent on each category,
        and within each category, print each Merchant, in descending order of the
        total spent with each Merchant.

            python -m chase file...
                """
            ),
        )

    def add_arguments(self) -> None:
        """Add arguments to parser."""

        arg = self.parser.add_argument(
            "--no-color",
            action="store_true",
            help="Do not print in color",
        )
        self.add_default_to_help(arg, self.parser)

        arg = self.parser.add_argument(
            "--no-exclude-chart-categories",
            action="store_true",
            help="Do not exclude select categories for charts",
        )
        self.add_default_to_help(arg, self.parser)

        arg = self.parser.add_argument(
            "--totals-only",
            action="store_true",
            help="Print totals only",
        )
        self.add_default_to_help(arg, self.parser)

        arg = self.parser.add_argument(
            "--averages-only",
            action="store_true",
            help=(
                "Print averages only (implies `--monthly`) "
                "(`--(bar|pie)chart` may also be given)"
            ),
        )
        self.add_default_to_help(arg, self.parser)

        arg = self.parser.add_argument(
            "--monthly",
            action="store_true",
            help="Generate a monthly report",
        )
        self.add_default_to_help(arg, self.parser)

        arg = self.parser.add_argument(
            "--category",
            help="Limit transactions to `CATEGORY`",
        )
        self.add_default_to_help(arg, self.parser)

        arg = self.parser.add_argument(
            "--barchart",
            action="store_true",
            help="Display a barchart of category totals",
        )
        self.add_default_to_help(arg, self.parser)

        arg = self.parser.add_argument(
            "--piechart",
            action="store_true",
            help="Display a piechart of category totals",
        )
        self.add_default_to_help(arg, self.parser)

        arg = self.parser.add_argument(
            "--detail",
            action="store_true",
            help="Include transaction details in the report",
        )
        self.add_default_to_help(arg, self.parser)

        arg = self.parser.add_argument(
            "--moving-average",
            action="store_true",
            help="Plot a moving average on the chart",
        )
        self.add_default_to_help(arg, self.parser)

        self.parser.add_argument(
            "-s",
            "--start",
            dest="start_date",
            help=self.dedent(
                """
    Print transactions at or after `start_date` (inclusive)
    (YYYY-MM-DD). Defaults to the epoch. Use `foy` to specify
    the first of this year.
                """
            ),
        )
        self.parser.add_argument(
            "-e",
            "--end",
            dest="end_date",
            help=self.dedent(
                """
    Print transactions prior to `end_date` (exclusive) (YYYY-MM-DD).
    Defaults to the end of time. Use `fom` to specify the first of
    this month.
                """
            ),
        )

        arg = self.parser.add_argument(
            "--use-datafiles",
            action="store_true",
            help="Process the CSV files defined in the config file",
        )
        self.add_default_to_help(arg, self.parser)

        self.parser.add_argument(
            "files",
            nargs="*",
            help="CSV files to process",
        )

    def main(self) -> None:
        """Command line interface entry point (method)."""

        if self.options.monthly and (self.options.barchart or self.options.piechart):
            self.options.averages_only = True
        elif self.options.averages_only:
            self.options.monthly = True

        # Read all `csv` files on the command line within the date range.
        chase = Chase(self.config, self.options)
        start, end = self._get_start_end_options()

        if self.options.use_datafiles and (datafiles := self.config.get("datafiles")):
            files = glob(str(Path(datafiles).expanduser()))
        else:
            files = self.options.files
        chase.read_input_files(files, start, end)

        # If start/end are undefined, set to the earliest/latest transactions.
        if not start or not end:
            earliest, latest = self._get_earliest_latest_transactions(chase)
            if not start:
                start = earliest
            if not end:
                end = latest

        nmonths = self._months_between(start, end)
        if self.options.barchart or self.options.piechart:
            _start = strftime("%Y-%m-%d", localtime(start))
            _end = strftime("%Y-%m-%d", localtime(end))
            chase.chart_title_date = f"over {nmonths} Months from {_start} to {_end}"

        # Print report.
        if self.options.monthly:
            chase.print_monthly_report(nmonths)
        elif self.options.barchart:
            chase.display_barchart_category_totals()
        elif self.options.piechart:
            chase.display_piechart_category_totals()
        else:
            chase.print_report()

    def _get_start_end_options(self) -> tuple[int, int]:
        """Return `--start` and `--end` command line options as a pair of integers."""

        start = self._parse_date(self.options.start_date) if self.options.start_date else 0
        end = self._parse_date(self.options.end_date) if self.options.end_date else 0
        return start, end

    def _get_earliest_latest_transactions(self, chase: Chase) -> tuple[int, int]:
        """Return earliest and latest transaction dates from the actual data."""

        earliest, latest = 0, 0
        for category_data in chase.categories.values():
            for merchant_data in category_data["merchants"].values():
                for row in merchant_data["transactions"]:
                    date = row["transaction_date"]
                    if not earliest or earliest > date:
                        earliest = date
                    if not latest or latest < date:
                        latest = date
        return earliest, latest

    def _parse_date(self, date_str: str) -> int:
        """Parse date string to Unix timestamp."""

        if date_str == "foy":
            # first of the year.
            st = localtime()
            return int(mktime((st.tm_year, 1, 1, 0, 0, 0, 0, 0, -1)))

        if date_str == "fom":
            # first of the month.
            st = localtime()
            return int(mktime((st.tm_year, st.tm_mon, 1, 0, 0, 0, 0, 0, -1)))

        return int(mktime(strptime(date_str, "%Y-%m-%d")))

    def _months_between(self, start: int, end: int) -> int:
        """Return the number of months between two Unix timestamps."""

        nmonths = 0
        while start < end:
            nmonths += 1
            st = localtime(start)
            start = int(mktime((st.tm_year, st.tm_mon + 1, st.tm_mday, 0, 0, 0, 0, 0, -1)))

        return nmonths


def main(args: list[str] | None = None) -> None:
    """Command line interface entry point (function)."""
    ChaseCLI(args).main()
