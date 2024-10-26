#!/usr/bin/env python3
"""Process downloaded account transaction files from Chase Bank."""

from __future__ import annotations

import csv
from argparse import Namespace
from collections import defaultdict
from time import localtime, mktime, strftime, strptime
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.container import BarContainer

__all__ = ["Chase"]


class Chase:
    """Process downloaded account transaction files from Chase Bank."""

    # pylint: disable=too-many-instance-attributes

    def __init__(self, config: dict[str, Any], options: Namespace) -> None:
        """Initialize new `Chase` object."""

        # Normalize merchants that start with...
        self.startswith_aliases = config.get("startswith_aliases", {})

        # Normalize merchants that contain...
        self.in_aliases = config.get("in_aliases", {})

        # Re-categorize these merchants...
        self.categories_by_merchant = config.get("categories_by_merchant", {})

        # Exclude these categories from charts.
        self.chart_exclude_categories = config.get("chart_exclude_categories", [])

        #
        self.options = options

        #
        if self.options.no_exclude_chart_categories:
            self.chart_exclude_categories = []

        #
        self.categories: dict[str, dict[str, Any]] = defaultdict(
            lambda: {  # key=category
                "total": 0,
                "count": 0,
                "merchants": defaultdict(
                    lambda: {  # key=merchant
                        "total": 0,
                        "count": 0,
                        "transactions": [],
                    }
                ),
                "monthly_totals": defaultdict(float),  # key="YYYY-MM"
                "monthly_average": 0,
                "monthly_avg2": 0,
            }
        )
        self.filenames_by_row: dict[str, str] = {}
        self.chart_title_date: str | None = None

    def is_excluded_from_charts(self, category: str) -> bool:
        """Return True if `category` is not for charts."""

        return (
            not self.options.no_exclude_chart_categories
            and category in self.chart_exclude_categories
        )

    def read_input_files(
        self,
        files: list[str],
        start: int,
        end: int,
    ) -> None:
        """Read all input files into memory."""

        for filename in files:
            with open(filename, encoding="utf-8") as fp:
                csv_reader = csv.DictReader(fp)
                self._read_csv_file(filename, start, end, csv_reader)

    def _read_csv_file(
        self,
        filename: str,
        start: int,
        end: int,
        csv_reader: Any,
    ) -> None:
        """Read and process a CSV file containing transaction data.

        Args:
            filename (str): The name of the file being processed.
            start (int): Unix timestamp for the start of the date range to process.
            end (int): Unix timestamp for the end of the date range to process.
            csv_reader (csv.DictReader): A CSV reader object for the file.

        This method processes each row in the CSV file, normalizes merchants,
        categorizes transactions, and accumulates totals and counts for reporting.
        """

        for row in csv_reader:
            # Credit-card accounts use `Transaction Date`.
            # Checking accounts use `Posting Date` and `Post Date`.
            # Skip transactions that are outside the date range.

            s_date = row.get("Transaction Date", row.get("Posting Date", row.get("Post Date")))
            date = int(mktime(strptime(s_date, "%m/%d/%Y")))
            if (start and date < start) or (end and date >= end):
                continue

            row["transaction_date"] = date

            # A single file may contain records that look like duplicates
            # of other records within the same file, but they're not; they
            # are unique transactions.
            #
            # The user, however, may submit .csv files with overlapping dates.
            # For example:
            #   file1: a .csv file for the trailing 90 days retrieved 1 month ago.
            #   file2: a .csv file for the trailing 90 days retrieved today.
            # The first 60 days of file2 overlap with the last 60 days of file1.
            #
            # Silently ignore cross-file duplicates.

            key = str(row)
            if key in self.filenames_by_row and filename != self.filenames_by_row[key]:
                continue
            self.filenames_by_row[key] = filename

            # Map aliases to normalized merchants.
            merchant = self._normalize_merchant(row["Description"])

            # Re-categorize some transactions.
            category = self.categories_by_merchant.get(
                merchant, row.get("Category", row.get("Type", "<None>"))
            )

            cdata = self.categories[category]
            amount = float(row["Amount"])

            cdata["total"] += amount
            cdata["count"] += 1
            cdata["merchants"][merchant]["total"] += amount
            cdata["merchants"][merchant]["count"] += 1
            cdata["merchants"][merchant]["transactions"].append(row)

            month = strftime("%Y-%m", localtime(date))
            cdata["monthly_totals"][month] += amount

    def _normalize_merchant(self, merchant: str) -> str:
        """Map aliases to normalized merchants."""

        merchant = merchant.upper()

        for alias, target in self.startswith_aliases.items():
            if merchant.startswith(alias):
                return str(target)

        for alias, target in self.in_aliases.items():
            if alias in merchant:
                return str(target)

        return merchant

    def print_report(self) -> None:
        """Print detailed report of transactions."""

        for category, cdata in sorted(
            self.categories.items(),
            key=lambda x: -abs(x[1]["total"]),
        ):

            if self.options.category is not None and self.options.category != category:
                # Limit transactions to `CATEGORY`.
                continue

            if not self.options.totals_only:
                print(self.color_text("category", f"{' ' + category:->80}"))
                self._print_report_merchants(cdata)

            print(
                self.color_text(
                    "total",
                    f"{cdata['total']:10.2f} {cdata['count']:10} Total {category}",
                )
            )

    def _print_report_merchants(self, cdata: dict[str, Any]) -> None:
        """Print the count and total of each merchant within `cdata`."""

        for merchant, mdata in sorted(
            cdata["merchants"].items(),
            key=lambda x: -abs(x[1]["total"]),
        ):
            if self.options.detail:
                for row in sorted(
                    mdata["transactions"],
                    key=lambda x: x.get("transaction_date"),
                ):
                    amount = float(row["Amount"])
                    date = strftime("%Y-%m-%d", localtime(row["transaction_date"]))
                    merchant = row["Description"]  # not normalized.
                    print(self.color_text("transaction", f"{amount:10.2f} {date} {merchant}"))

            print(
                self.color_text(
                    "subtotal",
                    f"{mdata['total']:10.2f} {mdata['count']:10} {merchant}",
                )
            )

    def print_monthly_report(self, nmonths: int) -> None:
        """Print a report of monthly totals for each category."""

        # pylint: disable=too-many-branches

        for category, cdata in sorted(
            self.categories.items(),
            key=lambda x: -abs(x[1]["total"]),
        ):

            if self.options.category is not None and self.options.category != category:
                # Limit transactions to `CATEGORY`.
                continue

            if not self.options.averages_only:
                print(self.color_text("category", f"{' ' + category:->80}"))

            monthly_totals = cdata["monthly_totals"]
            category_total = 0
            months = sorted(monthly_totals.keys())

            for month in months:
                total = monthly_totals[month]
                if not self.options.averages_only:
                    print(self.color_text("subtotal", f"{month} {total:10.2f}"))
                category_total += total

            if not self.options.averages_only:
                print(
                    self.color_text(
                        "total",
                        f"{category_total:18.2f}   Total {category} over {nmonths} months",
                    )
                )

            avg = category_total / nmonths
            cdata["monthly_average"] = avg
            print(
                self.color_text(
                    "average",
                    f"{avg:18.2f} Average {category} over {nmonths} months span",
                )
            )

            _nmonths = len(months)
            avg = category_total / _nmonths
            cdata["monthly_avg2"] = avg
            if not self.options.averages_only:
                print(
                    self.color_text(
                        "average",
                        f"{avg:18.2f} Average {category} over {_nmonths} months with data",
                    )
                )

            if self.options.detail and not self.options.averages_only:
                self._print_monthly_report_merchants(cdata)

        if self.options.category:
            if self.options.barchart:
                self.display_barchart_monthly_category()
            elif self.options.piechart:
                self.display_piechart_monthly_category()
        elif self.options.averages_only:
            if self.options.barchart:
                self.display_barchart_monthly_averages()
            elif self.options.piechart:
                self.display_piechart_monthly_averages()

    def _print_monthly_report_merchants(self, cdata: dict[str, Any]) -> None:
        """Print the count and total of each merchant within a `category`."""

        for merchant, mdata in sorted(
            cdata["merchants"].items(),
            key=lambda x: x[1]["total"],
        ):
            print(f"{mdata['total']:18.2f} {mdata['count']:5d} {merchant}")

    def _get_category_totals(self) -> tuple[list[str], list[int]]:
        """Return list of categories, and list of their associated totals."""

        categories = []
        totals = []

        for category, cdata in sorted(
            self.categories.items(),
            key=lambda x: -abs(x[1]["total"]),
        ):
            if self.is_excluded_from_charts(category):
                continue

            print(
                self.color_text(
                    "total",
                    f"{cdata['total']:10.2f} {cdata['count']:10} Total {category}",
                )
            )

            categories.append(category)
            totals.append(round(cdata["total"] * -1))

        return categories, totals

    def _get_monthly_averages(self) -> tuple[list[str], list[int]]:
        """Return list of categories, and list of their associated monthly averages."""

        categories = []
        averages = []

        for category, cdata in sorted(
            self.categories.items(),
            key=lambda x: -abs(x[1]["monthly_average"]),
        ):
            if self.is_excluded_from_charts(category):
                continue

            print(
                self.color_text(
                    "total",
                    f"{cdata['monthly_average']:10.2f} Monthly Average {category}",
                )
            )

            categories.append(category)
            averages.append(round(cdata["monthly_average"] * -1))

        return categories, averages

    def _get_monthly_totals(self, category: str) -> tuple[list[str], list[int]]:
        """Return list of months, and list of associated monthly totals, for given `category`."""

        cdata = self.categories[category]
        months = []
        totals = []

        for month, total in sorted(cdata["monthly_totals"].items()):
            months.append(month)
            totals.append(round(total * -1))

        return months, totals

    def display_barchart_category_totals(self) -> None:
        """Display a barchart of category totals."""

        categories, totals = self._get_category_totals()
        self._display_barchart("Categories", "Total", "Category Totals", categories, totals)

    def display_barchart_monthly_averages(self) -> None:
        """Display a barchart of monthly averages."""

        categories, averages = self._get_monthly_averages()
        self._display_barchart(
            "Categories", "Monthly Average", "Monthly Averages", categories, averages
        )

    def display_barchart_monthly_category(self) -> None:
        """Display a barchart of monthly totals for a given `--category CATEGORY`."""

        months, totals = self._get_monthly_totals(self.options.category)
        self._display_barchart(
            "Months", "Total", f"Monthly Totals for {self.options.category!r}", months, totals
        )

    def _display_barchart(
        self,
        xlabel: str,
        ylabel: str,
        title: str,
        xdata: list[str],
        ydata: list[int],
    ) -> None:
        # pylint: disable=too-many-arguments
        # pylint: disable=too-many-positional-arguments

        colors = plt.rcParams["axes.prop_cycle"].by_key()["color"]
        plt.figure(figsize=(12, 8))
        bars = plt.bar(xdata, ydata, color=colors)
        self._add_value_labels(bars)
        plt.xlabel(xlabel)
        plt.ylabel(ylabel)
        plt.title(f"{title} {self.chart_title_date}")
        plt.xticks(rotation=45, ha="right")
        plt.axhline(y=0, color="k", linestyle="-", linewidth=0.5)  # Add a line at y=0
        plt.tight_layout()

        if self.options.moving_average:
            df = pd.DataFrame({"value": ydata})
            window_size = min(4, len(ydata))
            moving_average = df["value"].rolling(window=window_size).mean()
            plt.plot(
                moving_average,
                color="red",
                linewidth=2,
                label=f"{window_size}-Month Moving Average",
            )
            plt.legend()

        plt.show()

    def _add_value_labels(self, bars: BarContainer) -> None:
        """Add value labels on the bars."""

        for _bar in bars:
            height = _bar.get_height()
            value = height  # The actual value
            x_pos = _bar.get_x() + _bar.get_width() / 2

            # Position labels based on bar height and sign
            if height >= 0:
                y_pos = height
                va = "bottom"
            else:
                y_pos = height
                va = "top"

            plt.text(x_pos, y_pos, f"${value}", ha="center", va=va)

    def display_piechart_category_totals(self) -> None:
        """Display a piechart of category totals."""

        categories, values = self._get_category_totals()
        self._display_piechart("Category Totals", categories, values)

    def display_piechart_monthly_averages(self) -> None:
        """Display a piechart of monthly averages."""

        categories, values = self._get_monthly_averages()
        self._display_piechart("Monthly Averages", categories, values)

    def display_piechart_monthly_category(self) -> None:
        """Display a piechart of monthly totals for a given `--category CATEGORY`."""

        months, totals = self._get_monthly_totals(self.options.category)
        self._display_piechart(f"Monthly Totals for {self.options.category!r}", months, totals)

    def _display_piechart(
        self,
        title: str,
        xdata: list[str],
        ydata: list[int],
    ) -> None:

        # pie() uses `plt.rcParams["axes.prop_cycle"].by_key()["color"]` by default.
        # plt.figure(figsize=(16, 9))  # 16:9 aspect ratio for widescreen displays
        # plt.figure(figsize=(10, 6))
        plt.figure(figsize=(12, 8))

        # Use absolute values for sizes
        abs_values = np.abs(ydata)

        # Sort wedges by absolute size for better visibility
        sorted_indices = np.argsort(abs_values)[::-1]
        sorted_categories = [xdata[i] for i in sorted_indices]
        sorted_abs_values = [abs_values[i] for i in sorted_indices]
        sorted_values = [ydata[i] for i in sorted_indices]

        # Create pie chart
        plt.pie(
            sorted_abs_values,
            labels=sorted_categories,
            autopct=lambda pct: f"{pct:.0f}%\n${sorted_values[sorted_categories.index(plt.gca().texts[-1].get_text())]}",  # noqa
            startangle=90,
            counterclock=False,
        )

        plt.title(f"{title} {self.chart_title_date}")
        plt.axis("equal")  # Equal aspect ratio ensures that pie is drawn as a circle
        plt.show()

    def color_text(self, color: str, text: str) -> str:
        """Apply color to the given text.

        Args:
            text (str): The text to color.
            color (str): The color to apply ('category', 'transaction', 'subtotal',
                                                'total', or 'average').

        Returns:
            str: The colored text.
        """

        if self.options.no_color:
            return text

        color_map = {
            "category": "0;38;5;61m",
            "transaction": "0;32m",  # green
            "subtotal": "0;36m",  # cyan
            "total": "0;33m",  # yellow
            "average": "0;32m",  # green
        }
        return f"\033[{color_map.get(color, '0m')}{text}\033[0m"
