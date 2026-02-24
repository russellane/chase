#!/usr/bin/env python3
"""Process downloaded account transaction files from Chase Bank."""

from __future__ import annotations

import csv
from argparse import Namespace
from collections import defaultdict
from dataclasses import dataclass, field
from time import localtime, mktime, strftime, strptime, time
from typing import Any

__all__ = ["Chase", "CategoryData", "MerchantData"]


@dataclass
class MerchantData:
    """Data for a single merchant within a category."""

    total: float = 0.0
    count: int = 0
    transactions: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class CategoryData:
    """Data for a single category."""

    total: float = 0.0
    count: int = 0
    merchants: dict[str, MerchantData] = field(default_factory=dict)
    monthly_totals: dict[str, float] = field(default_factory=dict)
    monthly_average: float = 0.0
    monthly_avg2: float = 0.0


class Chase:
    """Process downloaded account transaction files from Chase Bank."""

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

        self.options = options

        if self.options.no_exclude_chart_categories:
            self.chart_exclude_categories = []

        self.categories: dict[str, CategoryData] = {}
        self.filenames_by_row: dict[str, str] = {}
        self.chart_title_date: str | None = None

    def print_report(self) -> None:
        """Print the Category/Merchant Report."""

        for category, cdata in sorted(
            self.categories.items(),
            key=lambda x: -abs(x[1].total),
        ):
            if self.options.category is not None and self.options.category != category:
                # Limit transactions to `--category CATEGORY`.
                continue

            if not self.options.totals_only:
                print(self.color_text("category", f"{' ' + category:->80}"))
                self._print_report_merchants(cdata)

            print(
                self.color_text(
                    "total",
                    f"{cdata.total:10.2f} {cdata.count:10} Total {category}",
                )
            )

    def _print_report_merchants(self, cdata: CategoryData) -> None:
        """Print the count and total of each merchant within `cdata`."""

        for merchant, mdata in sorted(
            cdata.merchants.items(),
            key=lambda x: -abs(x[1].total),
        ):
            if self.options.detail:
                for row in sorted(
                    mdata.transactions,
                    key=lambda x: x["transaction_date"],
                ):
                    amount = float(row["Amount"])
                    date = strftime("%Y-%m-%d", localtime(row["transaction_date"]))
                    # PLW2901: overridden with un-normalized description for display.
                    merchant = row["Description"]  # noqa: PLW2901  # not normalized
                    print(self.color_text("transaction", f"{amount:10.2f} {date} {merchant}"))

            print(
                self.color_text(
                    "subtotal",
                    f"{mdata.total:10.2f} {mdata.count:10} {merchant}",
                )
            )

    def print_monthly_report(self, nmonths: int) -> None:
        """Print a report of monthly totals for each category."""

        for category, cdata in sorted(
            self.categories.items(),
            key=lambda x: -abs(x[1].total),
        ):
            if self.options.category is not None and self.options.category != category:
                # Limit transactions to `--category CATEGORY`.
                continue

            if not self.options.averages_only:
                print(self.color_text("category", f"{' ' + category:->80}"))

            monthly_totals = cdata.monthly_totals
            category_total = 0.0
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
            cdata.monthly_average = avg
            print(
                self.color_text(
                    "average",
                    f"{avg:18.2f} Average {category} over {nmonths} months span",
                )
            )

            _nmonths = len(months)
            avg = category_total / _nmonths
            cdata.monthly_avg2 = avg
            if not self.options.averages_only:
                print(
                    self.color_text(
                        "average",
                        f"{avg:18.2f} Average {category} over {_nmonths} months with data",
                    )
                )

            if self.options.detail and not self.options.averages_only:
                self._print_monthly_report_merchants(cdata)

    def _print_monthly_report_merchants(self, cdata: CategoryData) -> None:
        """Print the count and total of each merchant within a `category`."""

        for merchant, mdata in sorted(
            cdata.merchants.items(),
            key=lambda x: x[1].total,
        ):
            print(f"{mdata.total:18.2f} {mdata.count:5d} {merchant}")

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

            cdata = self.categories.setdefault(category, CategoryData())
            amount = float(row["Amount"])

            cdata.total += amount
            cdata.count += 1

            mdata = cdata.merchants.setdefault(merchant, MerchantData())
            mdata.total += amount
            mdata.count += 1
            mdata.transactions.append(row)

            month = strftime("%Y-%m", localtime(date))
            cdata.monthly_totals[month] = cdata.monthly_totals.get(month, 0.0) + amount

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

    def print_recurring_report(self) -> None:
        """Print detected recurring transactions (subscriptions and income)."""

        expenses = self._detect_recurring_merchants(income=False)
        income = self._detect_recurring_merchants(income=True)

        if not expenses and not income:
            print("No recurring transactions detected.")
            return

        total_expenses = 0.0
        total_income = 0.0

        # Print expenses section
        if expenses:
            expenses.sort(key=lambda x: -abs(x["annual_cost"]))

            print(self.color_text("category", "Recurring Transactions (Subscriptions)"))
            print(self.color_text("category", "-" * 50))
            print(
                self.color_text(
                    "subtotal",
                    f"{'Monthly':>8}  {'Amount':>10}  {'Annual Cost':>12}  Merchant",
                )
            )

            for item in expenses:
                count = item["count"]
                avg_amount = item["avg_amount"]
                annual_cost = item["annual_cost"]
                merchant = item["merchant"]
                total_expenses += annual_cost

                line = f"{count:>6}x   ${abs(avg_amount):>9.2f}   ${abs(annual_cost):>10.2f}"
                print(self.color_text("transaction", f"{line}  {merchant}"))

            print(self.color_text("category", "-" * 50))
            print(
                self.color_text(
                    "total",
                    f"{'':>8}  {'':>10}  ${abs(total_expenses):>10.2f}  Total Annual",
                )
            )

        # Print income section
        if income:
            income.sort(key=lambda x: -abs(x["annual_cost"]))

            if expenses:
                print()
            print(self.color_text("category", "Recurring Transactions (Income)"))
            print(self.color_text("category", "-" * 50))
            print(
                self.color_text(
                    "subtotal",
                    f"{'Monthly':>8}  {'Amount':>10}  {'Annual':>12}  Merchant",
                )
            )

            for item in income:
                count = item["count"]
                avg_amount = item["avg_amount"]
                annual_cost = item["annual_cost"]
                merchant = item["merchant"]
                total_income += annual_cost

                line = f"{count:>6}x   ${abs(avg_amount):>9.2f}   ${abs(annual_cost):>10.2f}"
                print(self.color_text("transaction", f"{line}  {merchant}"))

            print(self.color_text("category", "-" * 50))
            print(
                self.color_text(
                    "total",
                    f"{'':>8}  {'':>10}  ${abs(total_income):>10.2f}  Total Annual",
                )
            )

        # Print grand total
        if expenses and income:
            print()
            net_annual = total_income - total_expenses
            sign = "+" if net_annual >= 0 else "-"
            print(
                self.color_text(
                    "average",
                    f"{'':>8}  {'':>10}  {sign}${abs(net_annual):>9.2f}  Net Annual",
                )
            )

    def _detect_recurring_merchants(self, *, income: bool = False) -> list[dict[str, Any]]:
        """Detect merchants with recurring payment patterns.

        A merchant is considered recurring if:
        1. Appears in 3+ different months
        2. Has consistent amounts (within 20% tolerance)
        3. Appears roughly monthly (average interval between 20-40 days)
        4. Has a transaction within the last 2 years

        Args:
            income: If True, detect recurring income. If False, detect recurring expenses.

        Returns:
            List of dictionaries with merchant, count, avg_amount, annual_cost.
        """

        # Flatten all transactions by merchant (across categories)
        merchants_data: dict[str, list[dict[str, Any]]] = defaultdict(list)

        for category_data in self.categories.values():
            for merchant, mdata in category_data.merchants.items():
                merchants_data[merchant].extend(mdata.transactions)

        recurring = []
        for merchant, transactions in merchants_data.items():
            result = self._analyze_merchant_recurrence(merchant, transactions, income=income)
            if result:
                recurring.append(result)

        return recurring

    # Too many locals/returns; recurrence detection checks multiple orthogonal criteria inline.
    def _analyze_merchant_recurrence(  # noqa: PLR0914, PLR0911
        self, merchant: str, transactions: list[dict[str, Any]], *, income: bool = False
    ) -> dict[str, Any] | None:
        """Analyze a merchant's transactions for recurring patterns.

        Args:
            merchant: The merchant name.
            transactions: List of transaction dictionaries.
            income: If True, analyze income (positive amounts). If False, analyze expenses.

        Returns:
            Dictionary with merchant info if recurring, None otherwise.
        """

        if len(transactions) < 3:
            return None

        # Extract dates and amounts
        txn_data: list[tuple[int, float]] = []
        for txn in transactions:
            raw_amount = float(txn["Amount"])
            if income and raw_amount <= 0:  # Skip expenses when looking for income
                continue
            if not income and raw_amount >= 0:  # Skip income when looking for expenses
                continue
            date = txn["transaction_date"]
            amount = abs(raw_amount)
            txn_data.append((date, amount))

        if len(txn_data) < 3:
            return None

        # Filter out outliers: remove amounts < 50% of median
        amounts_only = sorted([amt for _, amt in txn_data])
        initial_median = amounts_only[len(amounts_only) // 2]
        txn_data = [(d, a) for d, a in txn_data if a >= initial_median * 0.5]

        if len(txn_data) < 3:
            return None

        # Rebuild lists after filtering
        months: set[str] = set()
        dates: list[int] = []
        amounts: list[float] = []

        for date, amount in txn_data:
            dates.append(date)
            amounts.append(amount)
            months.add(strftime("%Y-%m", localtime(date)))

        # Criterion 1: Must appear in 3+ different months
        if len(months) < 3:
            return None

        # Criterion 2: Check amount consistency (within 20% of median)
        amounts.sort()
        median_amount = amounts[len(amounts) // 2]

        if not all(abs(amt - median_amount) / median_amount <= 0.20 for amt in amounts):
            return None

        # Criterion 3: Check average interval is roughly monthly (20-40 days)
        dates.sort()
        if len(dates) >= 2:
            intervals = [(dates[i + 1] - dates[i]) / 86400 for i in range(len(dates) - 1)]
            avg_interval = sum(intervals) / len(intervals)
            if avg_interval < 20 or avg_interval > 40:
                return None

        # Criterion 4: Must have a transaction within the last 2 years
        two_years_ago = time() - (2 * 365 * 24 * 60 * 60)
        if dates[-1] < two_years_ago:
            return None

        # Calculate annual cost
        avg_amount = sum(amounts) / len(amounts)
        return {
            "merchant": merchant,
            "count": len(months),
            "avg_amount": avg_amount,
            "annual_cost": avg_amount * 12,
        }
