"""Tests for the portfolio module."""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from src import portfolio


@pytest.fixture(autouse=True)
def temp_portfolio(tmp_path):
    """Use a temporary portfolio file for each test."""
    test_file = tmp_path / "portfolio.json"
    with patch.object(portfolio, "PORTFOLIO_FILE", test_file):
        with patch.object(portfolio, "DATA_DIR", tmp_path):
            yield test_file


class TestAddHolding:
    """Tests for add_holding function."""

    def test_add_new_holding(self):
        result = portfolio.add_holding("AAPL", 10, 150.0)

        assert result["ticker"] == "AAPL"
        assert result["shares"] == 10
        assert result["avg_price"] == 150.0

    def test_add_to_existing_holding(self):
        portfolio.add_holding("AAPL", 10, 150.0)
        result = portfolio.add_holding("AAPL", 10, 160.0)

        assert result["shares"] == 20
        assert result["avg_price"] == 155.0

    def test_records_transaction(self):
        portfolio.add_holding("AAPL", 10, 150.0)
        transactions = portfolio.get_transactions("AAPL")

        assert len(transactions) == 1
        assert transactions[0]["type"] == "BUY"
        assert transactions[0]["shares"] == 10


class TestRemoveHolding:
    """Tests for remove_holding function."""

    def test_partial_sell(self):
        portfolio.add_holding("AAPL", 10, 150.0)
        result = portfolio.remove_holding("AAPL", 5, 160.0)

        assert result["shares"] == 5

    def test_full_sell(self):
        portfolio.add_holding("AAPL", 10, 150.0)
        result = portfolio.remove_holding("AAPL", 10, 160.0)

        assert result["shares"] == 0
        assert "message" in result

    def test_sell_nonexistent_raises(self):
        with pytest.raises(ValueError, match="No holding found"):
            portfolio.remove_holding("AAPL", 5, 150.0)

    def test_sell_too_many_raises(self):
        portfolio.add_holding("AAPL", 5, 150.0)
        with pytest.raises(ValueError, match="Cannot sell"):
            portfolio.remove_holding("AAPL", 10, 150.0)


class TestGetPortfolioSummary:
    """Tests for get_portfolio_summary function."""

    def test_empty_portfolio(self):
        summary = portfolio.get_portfolio_summary()

        assert summary["holdings"] == []
        assert summary["total_value"] == 0

    @patch("src.portfolio.get_stock_price")
    def test_with_holdings(self, mock_price):
        mock_price.return_value = {"price": 160.0}

        portfolio.add_holding("AAPL", 10, 150.0)
        summary = portfolio.get_portfolio_summary()

        assert len(summary["holdings"]) == 1
        assert summary["total_value"] == 1600.0
        assert summary["total_cost"] == 1500.0
        assert summary["total_gain"] == 100.0


class TestGetTransactions:
    """Tests for get_transactions function."""

    def test_empty_transactions(self):
        result = portfolio.get_transactions()
        assert result == []

    def test_filter_by_ticker(self):
        portfolio.add_holding("AAPL", 10, 150.0)
        portfolio.add_holding("GOOGL", 5, 2800.0)

        aapl_txns = portfolio.get_transactions("AAPL")
        assert len(aapl_txns) == 1
        assert aapl_txns[0]["ticker"] == "AAPL"
