"""Tests for the market_data module."""

from unittest.mock import patch, MagicMock

import pandas as pd
import pytest

from src.market_data import get_stock_price, get_historical_data, get_multiple_prices


@pytest.fixture
def mock_stock_data():
    """Create mock stock history data."""
    return pd.DataFrame({
        "Open": [150.0, 152.0],
        "High": [153.0, 155.0],
        "Low": [149.0, 151.0],
        "Close": [152.0, 154.0],
        "Volume": [1000000, 1200000],
    })


@pytest.fixture
def mock_stock_info():
    """Create mock stock info."""
    return {
        "shortName": "Apple Inc.",
        "currency": "USD",
        "marketCap": 2500000000000,
        "trailingPE": 28.5,
        "dividendYield": 0.006,
    }


class TestGetStockPrice:
    """Tests for get_stock_price function."""

    @patch("src.market_data.yf.Ticker")
    def test_returns_correct_price_data(self, mock_ticker, mock_stock_data, mock_stock_info):
        instance = mock_ticker.return_value
        instance.history.return_value = mock_stock_data
        instance.info = mock_stock_info

        result = get_stock_price("AAPL")

        assert result["ticker"] == "AAPL"
        assert result["price"] == 154.0
        assert result["name"] == "Apple Inc."
        assert result["currency"] == "USD"

    @patch("src.market_data.yf.Ticker")
    def test_calculates_change_correctly(self, mock_ticker, mock_stock_data, mock_stock_info):
        instance = mock_ticker.return_value
        instance.history.return_value = mock_stock_data
        instance.info = mock_stock_info

        result = get_stock_price("AAPL")

        assert result["change"] == 2.0
        assert result["change_pct"] == round((2.0 / 152.0) * 100, 2)

    @patch("src.market_data.yf.Ticker")
    def test_raises_on_empty_data(self, mock_ticker, mock_stock_info):
        instance = mock_ticker.return_value
        instance.history.return_value = pd.DataFrame()
        instance.info = mock_stock_info

        with pytest.raises(RuntimeError, match="Error fetching data"):
            get_stock_price("INVALID")


class TestGetHistoricalData:
    """Tests for get_historical_data function."""

    @patch("src.market_data.yf.Ticker")
    def test_returns_dataframe(self, mock_ticker, mock_stock_data):
        instance = mock_ticker.return_value
        instance.history.return_value = mock_stock_data

        result = get_historical_data("AAPL", period="1mo")

        assert isinstance(result, pd.DataFrame)
        assert "Close" in result.columns
        assert len(result) == 2

    @patch("src.market_data.yf.Ticker")
    def test_raises_on_empty_data(self, mock_ticker):
        instance = mock_ticker.return_value
        instance.history.return_value = pd.DataFrame()

        with pytest.raises(RuntimeError, match="Error fetching historical data"):
            get_historical_data("INVALID")


class TestGetMultiplePrices:
    """Tests for get_multiple_prices function."""

    @patch("src.market_data.get_stock_price")
    def test_returns_all_tickers(self, mock_get_price):
        mock_get_price.return_value = {"ticker": "AAPL", "price": 150.0}

        results = get_multiple_prices(["AAPL", "GOOGL"])

        assert len(results) == 2

    @patch("src.market_data.get_stock_price")
    def test_handles_errors_gracefully(self, mock_get_price):
        mock_get_price.side_effect = RuntimeError("API error")

        results = get_multiple_prices(["INVALID"])

        assert len(results) == 1
        assert "error" in results[0]
