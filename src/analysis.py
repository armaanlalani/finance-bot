"""Financial analysis module for calculating investment metrics."""

import numpy as np
import pandas as pd

from src.market_data import get_historical_data


def calculate_returns(ticker: str, period: str = "1y") -> dict:
    """Calculate return metrics for a given stock.

    Args:
        ticker: Stock ticker symbol.
        period: Historical period to analyze.

    Returns:
        Dictionary with return metrics.
    """
    data = get_historical_data(ticker, period=period)
    closes = data["Close"]

    total_return = (closes.iloc[-1] - closes.iloc[0]) / closes.iloc[0] * 100
    daily_returns = closes.pct_change().dropna()

    return {
        "ticker": ticker.upper(),
        "period": period,
        "total_return_pct": round(total_return, 2),
        "avg_daily_return_pct": round(daily_returns.mean() * 100, 4),
        "best_day_pct": round(daily_returns.max() * 100, 2),
        "worst_day_pct": round(daily_returns.min() * 100, 2),
        "positive_days": int((daily_returns > 0).sum()),
        "negative_days": int((daily_returns < 0).sum()),
    }


def calculate_volatility(ticker: str, period: str = "1y") -> dict:
    """Calculate volatility metrics for a given stock.

    Args:
        ticker: Stock ticker symbol.
        period: Historical period to analyze.

    Returns:
        Dictionary with volatility metrics.
    """
    data = get_historical_data(ticker, period=period)
    daily_returns = data["Close"].pct_change().dropna()

    daily_vol = daily_returns.std()
    annual_vol = daily_vol * np.sqrt(252)

    return {
        "ticker": ticker.upper(),
        "period": period,
        "daily_volatility_pct": round(daily_vol * 100, 4),
        "annual_volatility_pct": round(annual_vol * 100, 2),
        "max_drawdown_pct": round(_calculate_max_drawdown(data["Close"]) * 100, 2),
    }


def calculate_sharpe_ratio(
    ticker: str,
    period: str = "1y",
    risk_free_rate: float = 0.05,
) -> dict:
    """Calculate the Sharpe ratio for a given stock.

    Args:
        ticker: Stock ticker symbol.
        period: Historical period to analyze.
        risk_free_rate: Annual risk-free rate (default 5%).

    Returns:
        Dictionary with Sharpe ratio and components.
    """
    data = get_historical_data(ticker, period=period)
    daily_returns = data["Close"].pct_change().dropna()

    annual_return = daily_returns.mean() * 252
    annual_vol = daily_returns.std() * np.sqrt(252)

    sharpe = (annual_return - risk_free_rate) / annual_vol if annual_vol != 0 else 0.0

    return {
        "ticker": ticker.upper(),
        "period": period,
        "sharpe_ratio": round(sharpe, 4),
        "annualized_return_pct": round(annual_return * 100, 2),
        "annualized_volatility_pct": round(annual_vol * 100, 2),
        "risk_free_rate_pct": round(risk_free_rate * 100, 2),
    }


def compare_stocks(tickers: list[str], period: str = "1y") -> list[dict]:
    """Compare multiple stocks on key financial metrics.

    Args:
        tickers: List of stock ticker symbols to compare.
        period: Historical period to analyze.

    Returns:
        List of dictionaries with comparison metrics for each stock.
    """
    results = []
    for ticker in tickers:
        try:
            returns = calculate_returns(ticker, period)
            volatility = calculate_volatility(ticker, period)
            sharpe = calculate_sharpe_ratio(ticker, period)

            results.append({
                "ticker": ticker.upper(),
                "total_return_pct": returns["total_return_pct"],
                "annual_volatility_pct": volatility["annual_volatility_pct"],
                "max_drawdown_pct": volatility["max_drawdown_pct"],
                "sharpe_ratio": sharpe["sharpe_ratio"],
            })
        except RuntimeError as e:
            results.append({"ticker": ticker.upper(), "error": str(e)})

    return results


def _calculate_max_drawdown(prices: pd.Series) -> float:
    """Calculate the maximum drawdown from a price series.

    Args:
        prices: Series of stock prices.

    Returns:
        Maximum drawdown as a decimal (e.g., -0.15 for -15%).
    """
    cumulative_max = prices.cummax()
    drawdown = (prices - cumulative_max) / cumulative_max
    return drawdown.min()
