"""Utility functions for the finance bot."""

from datetime import datetime


def format_currency(value: float, currency: str = "USD") -> str:
    """Format a number as currency.

    Args:
        value: The numeric value to format.
        currency: Currency code (default 'USD').

    Returns:
        Formatted currency string.
    """
    symbols = {"USD": "$", "EUR": "€", "GBP": "£", "JPY": "¥", "CAD": "CA$"}
    symbol = symbols.get(currency, f"{currency} ")
    return f"{symbol}{value:,.2f}"


def format_percentage(value: float) -> str:
    """Format a number as a percentage with color indicator.

    Args:
        value: Percentage value.

    Returns:
        Formatted percentage string with +/- prefix.
    """
    prefix = "+" if value > 0 else ""
    return f"{prefix}{value:.2f}%"


def format_large_number(value: float | None) -> str:
    """Format a large number with K, M, B, T suffixes.

    Args:
        value: The numeric value to format.

    Returns:
        Formatted string with appropriate suffix.
    """
    if value is None:
        return "N/A"

    abs_value = abs(value)
    sign = "-" if value < 0 else ""

    if abs_value >= 1_000_000_000_000:
        return f"{sign}{abs_value / 1_000_000_000_000:.2f}T"
    elif abs_value >= 1_000_000_000:
        return f"{sign}{abs_value / 1_000_000_000:.2f}B"
    elif abs_value >= 1_000_000:
        return f"{sign}{abs_value / 1_000_000:.2f}M"
    elif abs_value >= 1_000:
        return f"{sign}{abs_value / 1_000:.2f}K"
    else:
        return f"{sign}{abs_value:.2f}"


def validate_ticker(ticker: str) -> str:
    """Validate and normalize a stock ticker symbol.

    Args:
        ticker: Raw ticker input string.

    Returns:
        Normalized uppercase ticker string.

    Raises:
        ValueError: If the ticker is invalid.
    """
    ticker = ticker.strip().upper()
    if not ticker:
        raise ValueError("Ticker symbol cannot be empty")
    if not ticker.replace(".", "").replace("-", "").isalnum():
        raise ValueError(f"Invalid ticker symbol: '{ticker}'")
    if len(ticker) > 10:
        raise ValueError(f"Ticker symbol too long: '{ticker}'")
    return ticker


def parse_date(date_str: str) -> datetime:
    """Parse a date string in common formats.

    Args:
        date_str: Date string to parse.

    Returns:
        Parsed datetime object.
    """
    formats = ["%Y-%m-%d", "%m/%d/%Y", "%d-%m-%Y", "%Y%m%d"]
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    raise ValueError(f"Unable to parse date: '{date_str}'. Use YYYY-MM-DD format.")
