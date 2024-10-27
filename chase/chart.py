#!/usr/bin/env python3
"""Process downloaded account transaction files from Chase Bank."""

from __future__ import annotations

from time import localtime, strftime

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.container import BarContainer

from chase.chase import Chase

__all__ = ["Chart"]


class Chart:
    """Provide charting methods."""

    def __init__(self, chase: Chase, nmonths: int, start: int, end: int) -> None:
        """Initialize object.

        Args:
            chase:      The data.
            nmonths:    The span of the data.
            start:      The start date of the data in unix time.
            end:        The end date of the data in unix time.
        """

        self.chase = chase
        self.start = start
        self.nmonths = nmonths
        self.end = end

    def _format_title(self, title: str) -> str:

        _start = strftime("%Y-%m-%d", localtime(self.start))
        _end = strftime("%Y-%m-%d", localtime(self.end))
        return f"{title} over {self.nmonths} Months from {_start} to {_end}"

    def display_category_totals(self) -> None:
        """Display a chart of category totals."""

        if self.chase.options.barchart:
            self._display_barchart_category_totals()
        elif self.chase.options.piechart:
            self._display_piechart_category_totals()

    def _display_barchart_category_totals(self) -> None:

        categories, totals = self._get_category_totals()
        self._display_barchart("Categories", "Total", "Category Totals", categories, totals)

    def _display_piechart_category_totals(self) -> None:

        categories, values = self._get_category_totals()
        self._display_piechart("Category Totals", categories, values)

    def _get_category_totals(self) -> tuple[list[str], list[int]]:
        """Return list of categories, and list of their associated totals."""

        categories = []
        totals = []

        for category, cdata in sorted(
            self.chase.categories.items(),
            key=lambda x: -abs(x[1]["total"]),
        ):
            if self._is_excluded_from_charts(category):
                continue

            print(
                self.chase.color_text(
                    "total",
                    f"{cdata['total']:10.2f} {cdata['count']:10} Total {category}",
                )
            )

            categories.append(category)
            totals.append(round(cdata["total"] * -1))

        return categories, totals

    def _is_excluded_from_charts(self, category: str) -> bool:
        """Return True if `category` is not for charts."""

        return (
            not self.chase.options.no_exclude_chart_categories
            and category in self.chase.chart_exclude_categories
        )

    # -------------------------------------------------------------------------------

    def display_monthly_averages(self) -> None:
        """Display a chart of monthly averages."""

        if self.chase.options.barchart:
            self._display_barchart_monthly_averages()
        elif self.chase.options.piechart:
            self._display_piechart_monthly_averages()

    def _display_barchart_monthly_averages(self) -> None:
        categories, averages = self._get_monthly_averages()
        self._display_barchart(
            "Categories", "Monthly Average", "Monthly Averages", categories, averages
        )

    def _display_piechart_monthly_averages(self) -> None:
        categories, values = self._get_monthly_averages()
        self._display_piechart("Monthly Averages", categories, values)

    def _get_monthly_averages(self) -> tuple[list[str], list[int]]:
        """Return list of categories, and list of their associated monthly averages."""

        categories = []
        averages = []

        for category, cdata in sorted(
            self.chase.categories.items(),
            key=lambda x: -abs(x[1]["monthly_average"]),
        ):
            if self._is_excluded_from_charts(category):
                continue

            print(
                self.chase.color_text(
                    "total",
                    f"{cdata['monthly_average']:10.2f} Monthly Average {category}",
                )
            )

            categories.append(category)
            averages.append(round(cdata["monthly_average"] * -1))

        return categories, averages

    # -------------------------------------------------------------------------------

    def display_monthly_category(self) -> None:
        """Display a chart of monthly totals for a given `--category CATEGORY`."""

        if self.chase.options.barchart:
            self._display_barchart_monthly_category()
        elif self.chase.options.piechart:
            self._display_piechart_monthly_category()

    def _display_barchart_monthly_category(self) -> None:

        months, totals = self._get_monthly_totals(self.chase.options.category)
        self._display_barchart(
            "Months",
            "Total",
            f"Monthly Totals for {self.chase.options.category!r}",
            months,
            totals,
        )

    def _display_piechart_monthly_category(self) -> None:

        months, totals = self._get_monthly_totals(self.chase.options.category)
        self._display_piechart(
            f"Monthly Totals for {self.chase.options.category!r}",
            months,
            totals,
        )

    def _get_monthly_totals(self, category: str) -> tuple[list[str], list[int]]:
        """Return list of months, and list of associated monthly totals, for given `category`."""

        cdata = self.chase.categories[category]
        months = []
        totals = []

        for month, total in sorted(cdata["monthly_totals"].items()):

            months.append(month)
            totals.append(round(total * -1))

        return months, totals

    # -------------------------------------------------------------------------------

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
        plt.title(self._format_title(title))
        plt.xticks(rotation=45, ha="right")
        plt.axhline(y=0, color="k", linestyle="-", linewidth=0.5)  # Add a line at y=0
        plt.tight_layout()

        if self.chase.options.moving_average:
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

        plt.title(self._format_title(title))
        plt.axis("equal")  # Equal aspect ratio ensures that pie is drawn as a circle
        plt.show()
