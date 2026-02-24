"""Command line interface."""

from glob import glob
from pathlib import Path
from time import localtime, mktime, strptime

from libcli import BaseCLI

from chase.chart import Chart
from chase.chase import Chase
from chase.interactive import ChaseApp

__all__ = ["ChaseCLI"]


class ChaseCLI(BaseCLI):
    """Command line-interface."""

    config = {
        "config-file": "~/.chase.toml",
        # distribution name, not importable package name
        "dist-name": "rlane-chase",
    }

    def init_parser(self) -> None:
        """Initialize argument parser."""

        self.ArgumentParser(
            prog=__package__,
            description=self.dedent("""
    Process downloaded Chase Bank transaction files.
                """),
        )

    def add_arguments(self) -> None:
        """Add arguments to parser."""

        group = self.parser.add_argument_group(
            "Category/Merchant Report",
            self.dedent("""
    By default, `%(prog)s` prints the Category/Merchant Report:

    List each Category, in descending order of the amount spent on each
    category.  Within each Category, list each Merchant, in descending
    order of the amount spent on each Merchant.
                """),
        )

        arg = group.add_argument(
            "--totals-only",
            action="store_true",
            help="List Categories and Totals only (suppress Merchants)",
        )
        self.add_default_to_help(arg, self.parser)

        arg = group.add_argument(
            "--detail",
            action="store_true",
            help="List Transactions under Merchants, in chronological order",
        )
        self.add_default_to_help(arg, self.parser)

        group = self.parser.add_argument_group(
            "Category Monthly Report",
            self.dedent("""
    List each Category, in descending order of the amount spent on each
    category.  Within each Category, list each Month, and the amount
    spent on the category that month.
                """),
        )

        arg = group.add_argument(
            "--monthly",
            action="store_true",
            help="Print Category Monthly Report",
        )
        self.add_default_to_help(arg, self.parser)

        arg = group.add_argument(
            "--averages-only",
            action="store_true",
            help=(
                "List averages only (implies `--monthly`) "
                "`--barchart` or `--piechart` may also be given)"
            ),
        )
        self.add_default_to_help(arg, self.parser)

        group = self.parser.add_argument_group("Charting options")

        chart_group = group.add_mutually_exclusive_group()

        arg = chart_group.add_argument(
            "--barchart",
            action="store_true",
            help="Display a barchart of the report",
        )
        self.add_default_to_help(arg, self.parser)

        arg = chart_group.add_argument(
            "--piechart",
            action="store_true",
            help="Display a piechart of the report",
        )
        self.add_default_to_help(arg, self.parser)

        arg = group.add_argument(
            "--moving-average",
            action="store_true",
            help="Plot a moving average on a barchart",
        )
        self.add_default_to_help(arg, self.parser)

        arg = group.add_argument(
            "--no-exclude-chart-categories",
            action="store_true",
            help=self.dedent("""
    Do not exclude select categories for charts. The categories are
    listed under `chart_exclude_categories` in the config file.
                """),
        )
        self.add_default_to_help(arg, self.parser)

        group = self.parser.add_argument_group("Filtering options")

        group.add_argument(
            "-s",
            "--start",
            dest="start_date",
            help=self.dedent("""
    Print transactions at or after `START_DATE` (inclusive)
    (YYYY-MM-DD). Defaults to the epoch. Use `foy` to specify
    the first of this year.
                """),
        )
        group.add_argument(
            "-e",
            "--end",
            dest="end_date",
            help=self.dedent("""
    Print transactions prior to `END_DATE` (exclusive) (YYYY-MM-DD).
    Defaults to the end of time. Use `fom` to specify the first of
    this month.
                """),
        )

        arg = group.add_argument(
            "--category",
            help=self.dedent("""
    Limit transactions to `CATEGORY`. If `--barchart` or `--piechart`
    are also given, then `--monthly` is implied.
                """),
        )
        self.add_default_to_help(arg, self.parser)

        group = self.parser.add_argument_group("Misc options")

        arg = group.add_argument(
            "--recurring",
            action="store_true",
            help="Detect and report recurring transactions (subscriptions)",
        )
        self.add_default_to_help(arg, self.parser)

        arg = group.add_argument(
            "--interactive",
            action="store_true",
            help="Launch interactive TUI for browsing transactions",
        )
        self.add_default_to_help(arg, self.parser)

        arg = group.add_argument(
            "--no-color",
            action="store_true",
            help="Do not print report in color",
        )
        self.add_default_to_help(arg, self.parser)

        group = self.parser.add_argument_group("Datafile options")

        arg = group.add_argument(
            "--use-datafiles",
            action="store_true",
            help="Process the `CSV` files defined under `datafiles` in the config file",
        )
        self.add_default_to_help(arg, self.parser)

        group.add_argument(
            "FILES",
            nargs="*",
            help="The `CSV` file(s) to process",
        )

        group = self.parser.add_argument_group(
            "Category Totals Chart",
            self.dedent("""
    Plot the Total amount spent on each category across the date-range,
    in descending order of the amount spent on each category.  This is a
    visualization of the Category/Merchant Report with `--totals-only`.
    Use `--barchart` or `--piechart` to display this chart.
                """),
        )

        group = self.parser.add_argument_group(
            "Monthly Averages Chart",
            self.dedent("""
    Plot the Average amount spent on each category per month, in
    descending order of the amount spent on each category.  This is a
    visualization of the Category Monthly Report with `--averages-only`.
    Use `--barchart` or `--piechart`, along with `--monthly` or
    `--averages-only`, to display this chart.
                """),
        )

        group = self.parser.add_argument_group(
            "Monthly Category Chart",
            self.dedent("""
    Plot the Amount spent each month on a given category.  Use
    `--barchart` or `--piechart`, along with `--category CATEGORY`,
    to display this chart.
                """),
        )

        group = self.parser.add_argument_group(
            "Configuration File",
            self.dedent("""
    The configuration file defines these elements:

        `datafiles` (str):  Points to the `CSV` files to process. May
                            begin with `~`, and may contain wildcards.

        `chart_exclude_categories` (list[str]): List of categories
                            to not plot on charts.

        `startswith_aliases` (mapping table): Map merchants that start
                            with the left-string to the right-string.

        `in_aliases` (mapping table): Map merchants that contain
                            the left-string to the right-string.

        `categories_by_merchant` (mapping table): Re-categorize the merchants
                            on the left to the Categories on the right.
                """),
        )

        group.add_argument(
            "--print-sample-config",
            action="store_true",
            help="Print a sample configuration file",
        )

    @property
    def charting(self) -> bool:
        """Return True if `--barchart` or `--piechart`."""
        return bool(self.options.barchart or self.options.piechart)

    # Too many branches; main dispatches over many mutually exclusive report and chart options.
    def main(self) -> None:  # noqa: PLR0912
        """Command line interface entry point (method)."""

        if self.options.print_sample_config:
            self._print_sample_config()
            self.parser.exit(0)

        if self.charting:
            if self.options.category:
                self.options.monthly = True
            if self.options.monthly:
                self.options.averages_only = True
            elif self.options.averages_only:
                self.options.monthly = True

        # Read all `csv` files on the command line within the date range.
        chase = Chase(self.config, self.options)
        start, end = self._get_start_end_options()
        if self.options.use_datafiles and (datafiles := self.config.get("datafiles")):
            files = glob(str(Path(datafiles).expanduser()))
        else:
            files = self.options.FILES
        chase.read_input_files(files, start, end)

        # If start/end are undefined, set to actual earliest/latest transactions.
        if not start or not end:
            earliest, latest = self._get_earliest_latest_transactions(chase)
            if not start:
                start = earliest
            if not end:
                end = latest

        # Determine the number of months covered.
        nmonths = self._months_between(start, end)

        # Output.
        if self.options.interactive:
            app = ChaseApp(chase, start, end)
            app.run()
            return

        if self.options.recurring:
            chase.print_recurring_report()
        elif self.charting:
            chart = Chart(chase, nmonths, start, end)

            if self.options.monthly:
                # Needed to analyze the data.
                chase.print_monthly_report(nmonths)

            if self.options.category:
                chart.display_monthly_category()
            elif self.options.averages_only:
                chart.display_monthly_averages()
            else:
                chart.display_category_totals()

        elif self.options.monthly:
            chase.print_monthly_report(nmonths)
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
            for merchant_data in category_data.merchants.values():
                for row in merchant_data.transactions:
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

    def _print_sample_config(self) -> None:
        print(
            self.dedent("""
    datafiles = "~/Documents/Chase/*CSV"

    # Exclude these categories from charts.
    chart_exclude_categories = [
        # "ACH_CREDIT",
        # "ACH_DEBIT",
    ]

    # Normalize merchants that start with...
    [startswith_aliases]
    # "AMZN Mktp US" = "AMZN Mktp US"
    # "NETFLIX  INC." = "NETFLIX.COM"

    # Normalize merchants that contain...
    [in_aliases]
    # "To The Northern Trust Co" = "Payment To The Northern Trust Co"

    # Re-categorize these merchants...
    [categories_by_merchant]
    # "APS electric pmt PAYMENTS" = "Bills & Utilities"
    # "CIRCLE K # 09529" = "Groceries"
            """)
        )


def main(args: list[str] | None = None) -> None:
    """Command line interface entry point (function)."""
    ChaseCLI(args).main()
