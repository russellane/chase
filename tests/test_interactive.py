"""Tests for the interactive TUI module."""

import sys
from argparse import Namespace
from time import mktime, strptime

import pytest
from pytest_mock.plugin import MockerFixture

from chase.chase import CategoryData, Chase, MerchantData
from chase.interactive import (
    CategoryList,
    ChaseApp,
    MerchantList,
    SummaryHeader,
    TransactionTable,
)


@pytest.fixture(name="mock_chase")
def fixture_mock_chase() -> Chase:
    """Create a mock Chase object with sample data."""

    config: dict[str, object] = {}
    options = Namespace(
        no_exclude_chart_categories=False,
        no_color=True,
        category=None,
        totals_only=False,
        detail=False,
    )
    chase = Chase(config, options)

    date1 = int(mktime(strptime("2024-01-15", "%Y-%m-%d")))
    date2 = int(mktime(strptime("2024-01-20", "%Y-%m-%d")))
    date3 = int(mktime(strptime("2024-02-10", "%Y-%m-%d")))

    chase.categories["Groceries"] = CategoryData(
        total=-150.00,
        count=3,
        merchants={
            "TRADER JOES": MerchantData(
                total=-100.00,
                count=2,
                transactions=[
                    {
                        "transaction_date": date1,
                        "Amount": "-45.67",
                        "Description": "TRADER JOES #123",
                    },
                    {
                        "transaction_date": date2,
                        "Amount": "-54.33",
                        "Description": "TRADER JOES #456",
                    },
                ],
            ),
            "WHOLE FOODS": MerchantData(
                total=-50.00,
                count=1,
                transactions=[
                    {
                        "transaction_date": date3,
                        "Amount": "-50.00",
                        "Description": "WHOLE FOODS MARKET",
                    },
                ],
            ),
        },
    )

    chase.categories["Gas"] = CategoryData(
        total=-80.00,
        count=2,
        merchants={
            "SHELL": MerchantData(
                total=-80.00,
                count=2,
                transactions=[
                    {"transaction_date": date1, "Amount": "-40.00", "Description": "SHELL OIL"},
                    {"transaction_date": date2, "Amount": "-40.00", "Description": "SHELL GAS"},
                ],
            ),
        },
    )

    return chase


@pytest.fixture(name="start_date")
def fixture_start_date() -> int:
    """Return start date as Unix timestamp."""

    return int(mktime(strptime("2024-01-01", "%Y-%m-%d")))


@pytest.fixture(name="end_date")
def fixture_end_date() -> int:
    """Return end date as Unix timestamp."""

    return int(mktime(strptime("2024-12-31", "%Y-%m-%d")))


def test_chase_app_initialization(mock_chase: Chase, start_date: int, end_date: int) -> None:
    """Test that ChaseApp initializes correctly."""

    app = ChaseApp(mock_chase, start_date, end_date)
    assert app._chase is mock_chase  # noqa: PLW212
    assert app._start == start_date  # noqa: PLW212
    assert app._end == end_date  # noqa: PLW212


def test_summary_header() -> None:
    """Test SummaryHeader widget creation."""

    start = int(mktime(strptime("2024-01-01", "%Y-%m-%d")))
    end = int(mktime(strptime("2024-12-31", "%Y-%m-%d")))
    header = SummaryHeader(start, end, -1234.56)
    assert header is not None


def test_summary_header_no_dates() -> None:
    """Test SummaryHeader with no dates."""

    header = SummaryHeader(0, 0, -500.00)
    assert header is not None


def test_category_list_creation(mock_chase: Chase) -> None:
    """Test CategoryList widget creation."""

    cat_list = CategoryList(mock_chase.categories)
    assert cat_list._categories is mock_chase.categories  # noqa: PLW212


def test_merchant_list_creation() -> None:
    """Test MerchantList widget creation."""

    merchant_list = MerchantList()
    assert not merchant_list.has_merchants()


def test_transaction_table_creation() -> None:
    """Test TransactionTable widget creation."""

    table = TransactionTable()
    assert table is not None


@pytest.mark.asyncio
async def test_app_compose(mock_chase: Chase, start_date: int, end_date: int) -> None:
    """Test that the app composes widgets correctly."""

    app = ChaseApp(mock_chase, start_date, end_date)
    async with app.run_test() as pilot:
        assert app.query_one(CategoryList) is not None
        assert app.query_one(MerchantList) is not None
        assert app.query_one(TransactionTable) is not None
        await pilot.pause()


@pytest.mark.asyncio
async def test_app_navigation(mock_chase: Chase, start_date: int, end_date: int) -> None:
    """Test keyboard navigation between panels."""

    app = ChaseApp(mock_chase, start_date, end_date)
    async with app.run_test() as pilot:
        category_list = app.query_one(CategoryList)
        merchant_list = app.query_one(MerchantList)
        transaction_table = app.query_one(TransactionTable)

        assert app.focused == category_list

        await pilot.press("enter")
        await pilot.pause()
        assert app.focused == merchant_list

        await pilot.press("enter")
        await pilot.pause()
        assert app.focused == transaction_table

        await pilot.press("escape")
        await pilot.pause()
        assert app.focused == merchant_list

        await pilot.press("escape")
        await pilot.pause()
        assert app.focused == category_list


@pytest.mark.asyncio
async def test_app_vim_navigation(mock_chase: Chase, start_date: int, end_date: int) -> None:
    """Test vim-style keyboard navigation."""

    app = ChaseApp(mock_chase, start_date, end_date)
    async with app.run_test() as pilot:
        category_list = app.query_one(CategoryList)
        merchant_list = app.query_one(MerchantList)

        assert app.focused == category_list

        await pilot.press("l")
        await pilot.pause()
        assert app.focused == merchant_list

        await pilot.press("h")
        await pilot.pause()
        assert app.focused == category_list


@pytest.mark.asyncio
async def test_app_cursor_movement(mock_chase: Chase, start_date: int, end_date: int) -> None:
    """Test j/k cursor movement."""

    app = ChaseApp(mock_chase, start_date, end_date)
    async with app.run_test() as pilot:
        category_list = app.query_one(CategoryList)

        assert category_list.index == 0

        await pilot.press("j")
        await pilot.pause()

        await pilot.press("k")
        await pilot.pause()


@pytest.mark.asyncio
async def test_app_quit(mock_chase: Chase, start_date: int, end_date: int) -> None:
    """Test quit action."""

    app = ChaseApp(mock_chase, start_date, end_date)
    async with app.run_test() as pilot:
        await pilot.press("q")


@pytest.mark.asyncio
async def test_category_selection_updates_merchants(
    mock_chase: Chase, start_date: int, end_date: int
) -> None:
    """Test that selecting a category updates the merchant list."""

    app = ChaseApp(mock_chase, start_date, end_date)
    async with app.run_test() as pilot:
        merchant_list = app.query_one(MerchantList)

        assert merchant_list.has_merchants()

        await pilot.press("down")
        await pilot.pause()


@pytest.mark.asyncio
async def test_merchant_selection_updates_transactions(
    mock_chase: Chase, start_date: int, end_date: int
) -> None:
    """Test that selecting a merchant updates the transaction table."""

    app = ChaseApp(mock_chase, start_date, end_date)
    async with app.run_test() as pilot:
        await pilot.press("enter")
        await pilot.pause()

        await pilot.press("down")
        await pilot.pause()


def test_interactive_cli_flag(mocker: MockerFixture) -> None:
    """Test that --interactive flag launches the TUI."""

    mock_run = mocker.patch("chase.interactive.ChaseApp.run")

    from chase.cli import ChaseCLI

    sys.argv = ["chase", "--interactive", "--use-datafiles"]
    ChaseCLI().main()

    mock_run.assert_called_once()


def test_category_list_get_selected_none() -> None:
    """Test get_selected_category returns None when no selection."""

    cat_list = CategoryList({})
    assert cat_list.get_selected_category() is None
    assert not cat_list.has_categories()
    assert cat_list.get_first_category_merchants() == {}


def test_merchant_list_get_selected_none() -> None:
    """Test get_selected_merchant returns None when no selection."""

    merchant_list = MerchantList()
    assert merchant_list.get_selected_merchant() is None
    assert merchant_list.get_selected_transactions() == []
    assert not merchant_list.has_merchants()
    assert merchant_list.get_first_merchant_transactions() == []


@pytest.mark.asyncio
async def test_vim_navigation_from_merchant_list(
    mock_chase: Chase, start_date: int, end_date: int
) -> None:
    """Test 'l' navigation from merchant list to transaction table."""

    app = ChaseApp(mock_chase, start_date, end_date)
    async with app.run_test() as pilot:
        merchant_list = app.query_one(MerchantList)
        transaction_table = app.query_one(TransactionTable)

        await pilot.press("l")
        await pilot.pause()
        assert app.focused == merchant_list

        await pilot.press("l")
        await pilot.pause()
        assert app.focused == transaction_table


@pytest.mark.asyncio
async def test_cursor_movement_on_datatable(
    mock_chase: Chase, start_date: int, end_date: int
) -> None:
    """Test j/k cursor movement on DataTable."""

    app = ChaseApp(mock_chase, start_date, end_date)
    async with app.run_test() as pilot:
        transaction_table = app.query_one(TransactionTable)

        await pilot.press("enter")
        await pilot.pause()
        await pilot.press("enter")
        await pilot.pause()

        assert app.focused == transaction_table

        await pilot.press("j")
        await pilot.pause()
        await pilot.press("k")
        await pilot.pause()


@pytest.mark.asyncio
async def test_merchant_list_get_selected_with_data(
    mock_chase: Chase, start_date: int, end_date: int
) -> None:
    """Test get_selected_merchant returns merchant name when selected."""

    app = ChaseApp(mock_chase, start_date, end_date)
    async with app.run_test() as pilot:
        merchant_list = app.query_one(MerchantList)

        await pilot.press("enter")
        await pilot.pause()

        assert merchant_list.index == 0
        selected = merchant_list.get_selected_merchant()
        assert selected is not None
