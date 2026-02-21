"""Market data module for fetching stock prices and financial data."""

from datetime import datetime, timedelta

import pandas as pd
import yfinance as yf

# Common exchange suffixes to try when a bare ticker fails
_EXCHANGE_SUFFIXES = ["", ".TO", ".V", ".L", ".AX", ".HK", ".DE"]


def resolve_ticker(ticker: str) -> str:
    """Try to resolve a ticker by testing common exchange suffixes.

    If the bare ticker has no data, tries appending exchange suffixes
    (e.g., .TO for TSX, .V for TSX Venture, .L for London).

    Args:
        ticker: Raw ticker symbol (e.g., 'XIC', 'AAPL').

    Returns:
        The working ticker string (e.g., 'XIC.TO').

    Raises:
        ValueError: If no valid ticker could be found.
    """
    ticker = ticker.strip().upper()

    # If it already has a suffix, use it directly
    if "." in ticker:
        return ticker

    for suffix in _EXCHANGE_SUFFIXES:
        candidate = f"{ticker}{suffix}"
        try:
            stock = yf.Ticker(candidate)
            history = stock.history(period="5d")
            if not history.empty:
                return candidate
        except Exception:
            continue

    raise ValueError(f"Could not find data for '{ticker}' on any exchange")


def get_stock_price(ticker: str) -> dict:
    """Fetch the current stock price and basic info for a given ticker.

    Args:
        ticker: Stock ticker symbol (e.g., 'AAPL', 'GOOGL').

    Returns:
        Dictionary containing current price, change, and basic info.
    """
    try:
        ticker = resolve_ticker(ticker)
        stock = yf.Ticker(ticker)
        info = stock.info
        history = stock.history(period="2d")

        if history.empty:
            raise ValueError(f"No data found for ticker '{ticker}'")

        current_price = history["Close"].iloc[-1]
        previous_close = history["Close"].iloc[-2] if len(history) > 1 else current_price
        change = current_price - previous_close
        change_pct = (change / previous_close) * 100

        return {
            "ticker": ticker.upper(),
            "price": round(current_price, 2),
            "change": round(change, 2),
            "change_pct": round(change_pct, 2),
            "name": info.get("shortName", ticker.upper()),
            "currency": info.get("currency", "USD"),
            "market_cap": info.get("marketCap"),
            "pe_ratio": info.get("trailingPE"),
            "dividend_yield": info.get("dividendYield"),
            "52w_high": info.get("fiftyTwoWeekHigh"),
            "52w_low": info.get("fiftyTwoWeekLow"),
            "sector": info.get("sector", ""),
            "industry": info.get("industry", ""),
            "description": info.get("longBusinessSummary", ""),
        }
    except Exception as e:
        raise RuntimeError(f"Error fetching data for '{ticker}': {e}")


def get_stock_detail(ticker: str) -> dict:
    """Fetch detailed stock/ETF information for the detail page.

    Args:
        ticker: Stock ticker symbol.

    Returns:
        Dictionary with comprehensive stock info.
    """
    try:
        ticker = resolve_ticker(ticker)
        stock = yf.Ticker(ticker)
        info = stock.info
        history = stock.history(period="1y")

        if history.empty:
            raise ValueError(f"No data found for ticker '{ticker}'")

        current_price = history["Close"].iloc[-1]
        previous_close = history["Close"].iloc[-2] if len(history) > 1 else current_price
        change = current_price - previous_close
        change_pct = (change / previous_close) * 100

        # Build sparkline data (last 30 days)
        recent = history["Close"].tail(30).tolist()
        chart_labels = [d.strftime("%b %d") for d in history.index[-30:]]

        return {
            "ticker": ticker.upper(),
            "name": info.get("shortName", ticker.upper()),
            "price": round(current_price, 2),
            "change": round(change, 2),
            "change_pct": round(change_pct, 2),
            "currency": info.get("currency", "USD"),
            "market_cap": info.get("marketCap"),
            "pe_ratio": info.get("trailingPE"),
            "forward_pe": info.get("forwardPE"),
            "dividend_yield": info.get("dividendYield"),
            "52w_high": info.get("fiftyTwoWeekHigh"),
            "52w_low": info.get("fiftyTwoWeekLow"),
            "avg_volume": info.get("averageVolume"),
            "beta": info.get("beta"),
            "sector": info.get("sector", "N/A"),
            "industry": info.get("industry", "N/A"),
            "description": info.get("longBusinessSummary", ""),
            "chart_prices": [round(p, 2) for p in recent],
            "chart_labels": chart_labels,
        }
    except Exception as e:
        raise RuntimeError(f"Error fetching detail for '{ticker}': {e}")


def get_historical_data(
    ticker: str,
    period: str = "1y",
    interval: str = "1d",
) -> pd.DataFrame:
    """Fetch historical price data for a given ticker.

    Args:
        ticker: Stock ticker symbol.
        period: Data period (e.g., '1d', '5d', '1mo', '3mo', '6mo', '1y', '5y', 'max').
        interval: Data interval (e.g., '1m', '5m', '1h', '1d', '1wk', '1mo').

    Returns:
        DataFrame with historical OHLCV data.
    """
    try:
        ticker = resolve_ticker(ticker)
        stock = yf.Ticker(ticker)
        history = stock.history(period=period, interval=interval)

        if history.empty:
            raise ValueError(f"No historical data found for '{ticker}'")

        return history
    except Exception as e:
        raise RuntimeError(f"Error fetching historical data for '{ticker}': {e}")


def get_multiple_prices(tickers: list[str]) -> list[dict]:
    """Fetch current prices for multiple tickers.

    Args:
        tickers: List of stock ticker symbols.

    Returns:
        List of dictionaries with price data for each ticker.
    """
    results = []
    for ticker in tickers:
        try:
            data = get_stock_price(ticker)
            results.append(data)
        except RuntimeError as e:
            results.append({"ticker": ticker.upper(), "error": str(e)})
    return results


def search_ticker(query: str) -> list[dict]:
    """Search for stock tickers matching a query string.

    Args:
        query: Search string (company name or partial ticker).

    Returns:
        List of matching tickers with basic info.
    """
    try:
        search = yf.Ticker(query)
        info = search.info
        if info and info.get("shortName"):
            return [{
                "ticker": query.upper(),
                "name": info.get("shortName", ""),
                "type": info.get("quoteType", ""),
                "exchange": info.get("exchange", ""),
            }]
        return []
    except Exception:
        return []
