"""Tests for the analysis module."""

from unittest.mock import patch

import numpy as np
import pandas as pd
import pytest

from src.analysis import (
    calculate_returns,
    calculate_volatility,
    calculate_sharpe_ratio,
    compare_stocks,
    _calculate_max_drawdown,
)


@pytest.fixture
def mock_historical_data():
    """Create mock historical price data."""
    dates = pd.date_range("2024-01-01", periods=252, freq="B")
    np.random.seed(42)
    prices = 100 * np.exp(np.cumsum(np.random.normal(0.0004, 0.015, 252)))

    return pd.DataFrame({
        "Open": prices * 0.99,
        "High": prices * 1.01,
        "Low": prices * 0.98,
        "Close": prices,
        "Volume": np.random.randint(1000000, 5000000, 252),
    }, index=dates)


class TestCalculateReturns:
    """Tests for calculate_returns function."""

    @patch("src.analysis.get_historical_data")
    def test_returns_expected_keys(self, mock_get_data, mock_historical_data):
        mock_get_data.return_value = mock_historical_data

        result = calculate_returns("AAPL")

        assert "ticker" in result
        assert "total_return_pct" in result
        assert "avg_daily_return_pct" in result
        assert "best_day_pct" in result
        assert "worst_day_pct" in result

    @patch("src.analysis.get_historical_data")
    def test_positive_return_for_uptrend(self, mock_get_data):
        data = pd.DataFrame({"Close": [100.0, 105.0, 110.0, 115.0, 120.0]})
        mock_get_data.return_value = data

        result = calculate_returns("AAPL")

        assert result["total_return_pct"] == 20.0


class TestCalculateVolatility:
    """Tests for calculate_volatility function."""

    @patch("src.analysis.get_historical_data")
    def test_returns_expected_keys(self, mock_get_data, mock_historical_data):
        mock_get_data.return_value = mock_historical_data

        result = calculate_volatility("AAPL")

        assert "daily_volatility_pct" in result
        assert "annual_volatility_pct" in result
        assert "max_drawdown_pct" in result

    @patch("src.analysis.get_historical_data")
    def test_volatility_is_positive(self, mock_get_data, mock_historical_data):
        mock_get_data.return_value = mock_historical_data

        result = calculate_volatility("AAPL")

        assert result["daily_volatility_pct"] > 0
        assert result["annual_volatility_pct"] > 0


class TestCalculateSharpeRatio:
    """Tests for calculate_sharpe_ratio function."""

    @patch("src.analysis.get_historical_data")
    def test_returns_expected_keys(self, mock_get_data, mock_historical_data):
        mock_get_data.return_value = mock_historical_data

        result = calculate_sharpe_ratio("AAPL")

        assert "sharpe_ratio" in result
        assert "annualized_return_pct" in result
        assert "risk_free_rate_pct" in result

    @patch("src.analysis.get_historical_data")
    def test_custom_risk_free_rate(self, mock_get_data, mock_historical_data):
        mock_get_data.return_value = mock_historical_data

        result = calculate_sharpe_ratio("AAPL", risk_free_rate=0.03)

        assert result["risk_free_rate_pct"] == 3.0


class TestCompareStocks:
    """Tests for compare_stocks function."""

    @patch("src.analysis.get_historical_data")
    def test_compares_multiple_stocks(self, mock_get_data, mock_historical_data):
        mock_get_data.return_value = mock_historical_data

        results = compare_stocks(["AAPL", "GOOGL"])

        assert len(results) == 2
        assert results[0]["ticker"] == "AAPL"
        assert results[1]["ticker"] == "GOOGL"


class TestMaxDrawdown:
    """Tests for _calculate_max_drawdown function."""

    def test_no_drawdown(self):
        prices = pd.Series([100, 110, 120, 130, 140])
        result = _calculate_max_drawdown(prices)
        assert result == 0.0

    def test_known_drawdown(self):
        prices = pd.Series([100, 120, 90, 110, 100])
        result = _calculate_max_drawdown(prices)
        assert result == pytest.approx(-0.25, abs=0.01)
