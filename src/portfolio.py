"""Portfolio management module for tracking holdings and transactions."""

import json
from datetime import datetime
from pathlib import Path

import pandas as pd

from src.config import DATA_DIR, PORTFOLIO_FILE
from src.market_data import get_stock_price


def _load_portfolio() -> dict:
    """Load portfolio data from the JSON file.

    Returns:
        Dictionary with portfolio holdings and transactions.
    """
    if not PORTFOLIO_FILE.exists():
        return {"holdings": {}, "transactions": []}

    with open(PORTFOLIO_FILE, "r") as f:
        return json.load(f)


def _save_portfolio(portfolio: dict) -> None:
    """Save portfolio data to the JSON file.

    Args:
        portfolio: Dictionary with portfolio holdings and transactions.
    """
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(PORTFOLIO_FILE, "w") as f:
        json.dump(portfolio, f, indent=2, default=str)


def add_holding(ticker: str, shares: float, price: float) -> dict:
    """Add a stock purchase to the portfolio.

    Args:
        ticker: Stock ticker symbol.
        shares: Number of shares purchased.
        price: Purchase price per share.

    Returns:
        Updated holding info for the ticker.
    """
    ticker = ticker.upper()
    portfolio = _load_portfolio()

    transaction = {
        "ticker": ticker,
        "type": "BUY",
        "shares": shares,
        "price": price,
        "total": round(shares * price, 2),
        "date": datetime.now().isoformat(),
    }
    portfolio["transactions"].append(transaction)

    if ticker in portfolio["holdings"]:
        holding = portfolio["holdings"][ticker]
        total_shares = holding["shares"] + shares
        total_cost = (holding["shares"] * holding["avg_price"]) + (shares * price)
        holding["shares"] = total_shares
        holding["avg_price"] = round(total_cost / total_shares, 2)
    else:
        portfolio["holdings"][ticker] = {
            "shares": shares,
            "avg_price": price,
        }

    _save_portfolio(portfolio)
    return {"ticker": ticker, **portfolio["holdings"][ticker]}


def remove_holding(ticker: str, shares: float, price: float) -> dict:
    """Record a stock sale from the portfolio.

    Args:
        ticker: Stock ticker symbol.
        shares: Number of shares sold.
        price: Sale price per share.

    Returns:
        Updated holding info or confirmation of full sale.
    """
    ticker = ticker.upper()
    portfolio = _load_portfolio()

    if ticker not in portfolio["holdings"]:
        raise ValueError(f"No holding found for '{ticker}'")

    holding = portfolio["holdings"][ticker]
    if shares > holding["shares"]:
        raise ValueError(
            f"Cannot sell {shares} shares of {ticker}. Only {holding['shares']} shares held."
        )

    transaction = {
        "ticker": ticker,
        "type": "SELL",
        "shares": shares,
        "price": price,
        "total": round(shares * price, 2),
        "date": datetime.now().isoformat(),
    }
    portfolio["transactions"].append(transaction)

    holding["shares"] -= shares
    if holding["shares"] <= 0:
        del portfolio["holdings"][ticker]
        _save_portfolio(portfolio)
        return {"ticker": ticker, "shares": 0, "message": "Position fully closed"}

    portfolio["holdings"][ticker] = holding
    _save_portfolio(portfolio)
    return {"ticker": ticker, **holding}


def get_portfolio_summary() -> dict:
    """Get a summary of all current portfolio holdings with live prices.

    Returns:
        Dictionary with holdings, total value, and performance metrics.
    """
    portfolio = _load_portfolio()
    holdings = portfolio.get("holdings", {})

    if not holdings:
        return {"holdings": [], "total_value": 0, "total_cost": 0, "total_gain": 0, "total_gain_pct": 0}

    summary_holdings = []
    total_value = 0.0
    total_cost = 0.0

    for ticker, holding in holdings.items():
        try:
            live = get_stock_price(ticker)
            current_price = live["price"]
        except RuntimeError:
            current_price = holding["avg_price"]

        market_value = round(holding["shares"] * current_price, 2)
        cost_basis = round(holding["shares"] * holding["avg_price"], 2)
        gain = round(market_value - cost_basis, 2)
        gain_pct = round((gain / cost_basis) * 100, 2) if cost_basis else 0.0

        summary_holdings.append({
            "ticker": ticker,
            "shares": holding["shares"],
            "avg_price": holding["avg_price"],
            "current_price": current_price,
            "market_value": market_value,
            "cost_basis": cost_basis,
            "gain": gain,
            "gain_pct": gain_pct,
        })

        total_value += market_value
        total_cost += cost_basis

    total_gain = round(total_value - total_cost, 2)
    total_gain_pct = round((total_gain / total_cost) * 100, 2) if total_cost else 0.0

    return {
        "holdings": summary_holdings,
        "total_value": round(total_value, 2),
        "total_cost": round(total_cost, 2),
        "total_gain": total_gain,
        "total_gain_pct": total_gain_pct,
    }


def get_transactions(ticker: str | None = None) -> list[dict]:
    """Get transaction history, optionally filtered by ticker.

    Args:
        ticker: Optional ticker to filter transactions.

    Returns:
        List of transaction records.
    """
    portfolio = _load_portfolio()
    transactions = portfolio.get("transactions", [])

    if ticker:
        ticker = ticker.upper()
        transactions = [t for t in transactions if t["ticker"] == ticker]

    return transactions
