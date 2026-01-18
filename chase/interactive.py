"""Interactive TUI for browsing Chase transaction data."""

from __future__ import annotations

from time import localtime, strftime
from typing import TYPE_CHECKING, Any

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal
from textual.widgets import DataTable, Footer, Header, ListItem, ListView, Static

if TYPE_CHECKING:
    from chase.chase import Chase

__all__ = ["ChaseApp"]


class CategoryList(ListView):
    """Left panel showing categories."""

    BORDER_TITLE = "Categories"

    def __init__(self, categories: dict[str, dict[str, Any]]) -> None:
        """Initialize category list."""

        super().__init__()
        self._categories = categories
        self._sorted_categories: list[tuple[str, dict[str, Any]]] = []

    def on_mount(self) -> None:
        """Populate the list when mounted."""

        self._sorted_categories = sorted(
            self._categories.items(),
            key=lambda x: -abs(x[1]["total"]),
        )
        for category, cdata in self._sorted_categories:
            total = cdata["total"]
            label = f"{category[:18]:<18} ${abs(total):>10,.2f}"
            self.append(ListItem(Static(label)))

    def get_selected_category(self) -> str | None:
        """Return the currently selected category name."""

        if self.index is not None and 0 <= self.index < len(self._sorted_categories):
            return self._sorted_categories[self.index][0]
        return None

    def has_categories(self) -> bool:
        """Return True if there are categories loaded."""

        return len(self._sorted_categories) > 0

    def get_first_category_merchants(self) -> dict[str, dict[str, Any]]:
        """Return merchants for the first category."""

        if self._sorted_categories:
            return dict(self._sorted_categories[0][1]["merchants"])
        return {}


class MerchantList(ListView):
    """Middle panel showing merchants for selected category."""

    BORDER_TITLE = "Merchants"

    def __init__(self) -> None:
        """Initialize merchant list."""

        super().__init__()
        self._merchants: list[tuple[str, dict[str, Any]]] = []

    def update_merchants(self, merchants: dict[str, dict[str, Any]]) -> None:
        """Update the merchant list for a selected category."""

        self.clear()
        self._merchants = sorted(
            merchants.items(),
            key=lambda x: -abs(x[1]["total"]),
        )
        for merchant, mdata in self._merchants:
            total = mdata["total"]
            count = mdata["count"]
            label = f"{merchant[:18]:<18} ${abs(total):>8,.2f} ({count})"
            self.append(ListItem(Static(label)))

        if self._merchants:
            self.index = 0

    def get_selected_merchant(self) -> str | None:
        """Return the currently selected merchant name."""

        if self.index is not None and 0 <= self.index < len(self._merchants):
            return self._merchants[self.index][0]
        return None

    def get_selected_transactions(self) -> list[dict[str, Any]]:
        """Return transactions for the selected merchant."""

        if self.index is not None and 0 <= self.index < len(self._merchants):
            return list(self._merchants[self.index][1]["transactions"])
        return []

    def has_merchants(self) -> bool:
        """Return True if there are merchants loaded."""

        return len(self._merchants) > 0

    def get_first_merchant_transactions(self) -> list[dict[str, Any]]:
        """Return transactions for the first merchant."""

        if self._merchants:
            return list(self._merchants[0][1]["transactions"])
        return []


class TransactionTable(DataTable[str]):
    """Right panel showing transactions for selected merchant."""

    BORDER_TITLE = "Transactions"

    def __init__(self) -> None:
        """Initialize transaction table."""

        super().__init__()

    def on_mount(self) -> None:
        """Set up columns when mounted."""

        self.add_columns("Date", "Amount", "Description")
        self.cursor_type = "row"

    def update_transactions(self, transactions: list[dict[str, Any]]) -> None:
        """Update the transaction table."""

        self.clear()
        sorted_transactions = sorted(
            transactions,
            key=lambda x: x.get("transaction_date", 0),
            reverse=True,
        )
        for txn in sorted_transactions:
            date = txn.get("transaction_date", 0)
            date_str = strftime("%Y-%m-%d", localtime(date)) if date else "N/A"
            amount = float(txn.get("Amount", 0))
            desc = txn.get("Description", "")[:30]
            self.add_row(date_str, f"${amount:>10,.2f}", desc)


class SummaryHeader(Static):
    """Header showing date range and total spending."""

    def __init__(self, start: int, end: int, total: float) -> None:
        """Initialize summary header."""

        start_str = strftime("%Y-%m-%d", localtime(start)) if start else "Start"
        end_str = strftime("%Y-%m-%d", localtime(end)) if end else "End"
        content = f"Chase Transactions | {start_str} to {end_str} | Total: ${abs(total):,.2f}"
        super().__init__(content)


class ChaseApp(App[None]):
    """Textual app for browsing Chase transaction data."""

    CSS = """
    Screen {
        layout: grid;
        grid-size: 1;
        grid-rows: auto 1fr auto;
    }

    #header-container {
        height: auto;
        padding: 1;
        background: $primary;
        text-align: center;
    }

    #main-container {
        height: 1fr;
    }

    CategoryList {
        width: 1fr;
        border: solid $primary;
        padding: 0 1;
    }

    MerchantList {
        width: 1fr;
        border: solid $secondary;
        padding: 0 1;
    }

    TransactionTable {
        width: 2fr;
        border: solid $accent;
        padding: 0 1;
    }

    ListView > ListItem.--highlight {
        background: $accent;
    }

    Footer {
        background: $surface;
    }
    """

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("escape", "focus_previous_panel", "Back", show=True),
        Binding("h", "focus_previous_panel", "Back", show=False),
        Binding("l", "focus_next_panel", "Select", show=False),
        Binding("j", "cursor_down", "Down", show=False),
        Binding("k", "cursor_up", "Up", show=False),
    ]

    def __init__(self, chase: "Chase", start: int, end: int) -> None:
        """Initialize the app with Chase data."""

        super().__init__()
        self._chase = chase
        self._start = start
        self._end = end
        self._total = sum(cdata["total"] for cdata in chase.categories.values())
        self._category_list: CategoryList | None = None
        self._merchant_list: MerchantList | None = None
        self._transaction_table: TransactionTable | None = None

    def compose(self) -> ComposeResult:
        """Create child widgets."""

        yield Header()
        yield Container(
            SummaryHeader(self._start, self._end, self._total),
            id="header-container",
        )
        yield Horizontal(
            CategoryList(self._chase.categories),
            MerchantList(),
            TransactionTable(),
            id="main-container",
        )
        yield Footer()

    def on_mount(self) -> None:
        """Set up the app when mounted."""

        self._category_list = self.query_one(CategoryList)
        self._merchant_list = self.query_one(MerchantList)
        self._transaction_table = self.query_one(TransactionTable)

        self._category_list.focus()

        if self._category_list.has_categories():
            merchants = self._category_list.get_first_category_merchants()
            self._merchant_list.update_merchants(merchants)

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        """Handle list item selection and move focus to next panel."""

        if isinstance(event.list_view, CategoryList) and self._category_list:
            category = self._category_list.get_selected_category()
            if category and self._merchant_list:
                merchants = self._chase.categories[category]["merchants"]
                self._merchant_list.update_merchants(merchants)
                if self._transaction_table:
                    self._transaction_table.clear()
                self._merchant_list.focus()

        elif isinstance(event.list_view, MerchantList) and self._merchant_list:
            transactions = self._merchant_list.get_selected_transactions()
            if self._transaction_table:
                self._transaction_table.update_transactions(transactions)
                self._transaction_table.focus()

    def on_list_view_highlighted(self, event: ListView.Highlighted) -> None:
        """Handle list item highlight (cursor movement)."""

        if isinstance(event.list_view, CategoryList) and self._category_list:
            category = self._category_list.get_selected_category()
            if category and self._merchant_list:
                merchants = self._chase.categories[category]["merchants"]
                self._merchant_list.update_merchants(merchants)
                if self._transaction_table:
                    self._transaction_table.clear()
                    if self._merchant_list.has_merchants():
                        txns = self._merchant_list.get_first_merchant_transactions()
                        self._transaction_table.update_transactions(txns)

        elif isinstance(event.list_view, MerchantList) and self._merchant_list:
            transactions = self._merchant_list.get_selected_transactions()
            if self._transaction_table:
                self._transaction_table.update_transactions(transactions)

    def action_focus_next_panel(self) -> None:
        """Move focus to the next panel."""

        focused = self.focused
        if focused == self._category_list and self._merchant_list:
            self._merchant_list.focus()
        elif focused == self._merchant_list and self._transaction_table:
            self._transaction_table.focus()

    def action_focus_previous_panel(self) -> None:
        """Move focus to the previous panel."""

        focused = self.focused
        if focused == self._transaction_table and self._merchant_list:
            self._merchant_list.focus()
        elif focused == self._merchant_list and self._category_list:
            self._category_list.focus()

    def action_cursor_down(self) -> None:
        """Move cursor down in the focused list."""

        focused = self.focused
        if isinstance(focused, (ListView, DataTable)):
            focused.action_cursor_down()

    def action_cursor_up(self) -> None:
        """Move cursor up in the focused list."""

        focused = self.focused
        if isinstance(focused, (ListView, DataTable)):
            focused.action_cursor_up()
