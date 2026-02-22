"""Portfolio management module for tracking holdings and transactions."""

import csv
import io
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


def _holding_key(ticker: str, account_type: str) -> str:
    """Create a unique key for a holding combining ticker and account type.

    Args:
        ticker: Stock ticker symbol.
        account_type: Account type (e.g., TFSA, FHSA, Non-registered).

    Returns:
        String key like 'AAPL::TFSA'.
    """
    return f"{ticker}::{account_type}"


def _parse_holding_key(key: str) -> tuple[str, str]:
    """Parse a holding key back into ticker and account type.

    Args:
        key: Holding key like 'AAPL::TFSA'.

    Returns:
        Tuple of (ticker, account_type).
    """
    if "::" in key:
        parts = key.split("::", 1)
        return parts[0], parts[1]
    # Legacy key without account type
    return key, "Unspecified"


ACCOUNT_TYPES = [
    "TFSA",
    "RRSP",
    "FHSA",
    "Non-registered",
    "RESP",
    "LIRA",
    "Corporate",
    "Unspecified",
]


def _migrate_portfolio(portfolio: dict) -> dict:
    """Migrate legacy portfolio data to include account_type.

    Converts old-style holdings keyed by ticker to new-style keyed by
    'TICKER::account_type'. Also adds account_type to transactions.

    Args:
        portfolio: Portfolio dict that may have legacy format.

    Returns:
        Migrated portfolio dict.
    """
    migrated = False
    new_holdings = {}

    for key, holding in list(portfolio.get("holdings", {}).items()):
        if "::" not in key:
            # Legacy holding without account type
            new_key = _holding_key(key, holding.get("account_type", "Unspecified"))
            holding.setdefault("account_type", "Unspecified")
            new_holdings[new_key] = holding
            migrated = True
        else:
            holding.setdefault("account_type", _parse_holding_key(key)[1])
            new_holdings[key] = holding

    if migrated:
        portfolio["holdings"] = new_holdings

    # Ensure all transactions have account_type
    for tx in portfolio.get("transactions", []):
        tx.setdefault("account_type", "Unspecified")

    return portfolio


def add_holding(ticker: str, shares: float, price: float, account_type: str = "Unspecified") -> dict:
    """Add a stock purchase to the portfolio.

    Args:
        ticker: Stock ticker symbol.
        shares: Number of shares purchased.
        price: Purchase price per share.
        account_type: Account type (e.g., TFSA, FHSA, Non-registered).

    Returns:
        Updated holding info for the ticker.
    """
    ticker = ticker.upper()
    portfolio = _load_portfolio()
    portfolio = _migrate_portfolio(portfolio)

    transaction = {
        "ticker": ticker,
        "type": "BUY",
        "shares": shares,
        "price": price,
        "total": round(shares * price, 2),
        "date": datetime.now().isoformat(),
        "account_type": account_type,
    }
    portfolio["transactions"].append(transaction)

    key = _holding_key(ticker, account_type)
    if key in portfolio["holdings"]:
        holding = portfolio["holdings"][key]
        total_shares = holding["shares"] + shares
        total_cost = (holding["shares"] * holding["avg_price"]) + (shares * price)
        holding["shares"] = total_shares
        holding["avg_price"] = round(total_cost / total_shares, 2)
    else:
        portfolio["holdings"][key] = {
            "shares": shares,
            "avg_price": price,
            "account_type": account_type,
        }

    _save_portfolio(portfolio)
    return {"ticker": ticker, "account_type": account_type, **portfolio["holdings"][key]}


def remove_holding(ticker: str, shares: float, price: float, account_type: str = "Unspecified") -> dict:
    """Record a stock sale from the portfolio.

    Args:
        ticker: Stock ticker symbol.
        shares: Number of shares sold.
        price: Sale price per share.
        account_type: Account type (e.g., TFSA, FHSA, Non-registered).

    Returns:
        Updated holding info or confirmation of full sale.
    """
    ticker = ticker.upper()
    portfolio = _load_portfolio()
    portfolio = _migrate_portfolio(portfolio)

    key = _holding_key(ticker, account_type)
    if key not in portfolio["holdings"]:
        raise ValueError(f"No holding found for '{ticker}' in {account_type}")

    holding = portfolio["holdings"][key]
    if shares > holding["shares"]:
        raise ValueError(
            f"Cannot sell {shares} shares of {ticker} in {account_type}. Only {holding['shares']} shares held."
        )

    transaction = {
        "ticker": ticker,
        "type": "SELL",
        "shares": shares,
        "price": price,
        "total": round(shares * price, 2),
        "date": datetime.now().isoformat(),
        "account_type": account_type,
    }
    portfolio["transactions"].append(transaction)

    holding["shares"] -= shares
    if holding["shares"] <= 0:
        del portfolio["holdings"][key]
        _save_portfolio(portfolio)
        return {"ticker": ticker, "account_type": account_type, "shares": 0, "message": "Position fully closed"}

    portfolio["holdings"][key] = holding
    _save_portfolio(portfolio)
    return {"ticker": ticker, "account_type": account_type, **holding}


def get_portfolio_summary() -> dict:
    """Get a summary of all current portfolio holdings with live prices.

    Returns:
        Dictionary with holdings grouped by account type, total value, and performance metrics.
    """
    portfolio = _load_portfolio()
    portfolio = _migrate_portfolio(portfolio)
    holdings = portfolio.get("holdings", {})

    if not holdings:
        return {"holdings": [], "total_value": 0, "total_cost": 0, "total_gain": 0, "total_gain_pct": 0, "accounts": {}}

    summary_holdings = []
    total_value = 0.0
    total_cost = 0.0
    accounts: dict[str, dict] = {}

    for key, holding in holdings.items():
        ticker, account_type = _parse_holding_key(key)
        account_type = holding.get("account_type", account_type)

        try:
            live = get_stock_price(ticker)
            current_price = live["price"]
        except RuntimeError:
            current_price = holding["avg_price"]

        market_value = round(holding["shares"] * current_price, 2)
        cost_basis = round(holding["shares"] * holding["avg_price"], 2)
        gain = round(market_value - cost_basis, 2)
        gain_pct = round((gain / cost_basis) * 100, 2) if cost_basis else 0.0

        holding_data = {
            "ticker": ticker,
            "account_type": account_type,
            "shares": holding["shares"],
            "avg_price": holding["avg_price"],
            "current_price": current_price,
            "market_value": market_value,
            "cost_basis": cost_basis,
            "gain": gain,
            "gain_pct": gain_pct,
        }
        summary_holdings.append(holding_data)

        # Accumulate per-account totals
        if account_type not in accounts:
            accounts[account_type] = {"total_value": 0.0, "total_cost": 0.0}
        accounts[account_type]["total_value"] += market_value
        accounts[account_type]["total_cost"] += cost_basis

        total_value += market_value
        total_cost += cost_basis

    # Compute per-account gain/pct
    for acct, data in accounts.items():
        data["total_gain"] = round(data["total_value"] - data["total_cost"], 2)
        data["total_gain_pct"] = (
            round((data["total_gain"] / data["total_cost"]) * 100, 2)
            if data["total_cost"]
            else 0.0
        )
        data["total_value"] = round(data["total_value"], 2)
        data["total_cost"] = round(data["total_cost"], 2)

    total_gain = round(total_value - total_cost, 2)
    total_gain_pct = round((total_gain / total_cost) * 100, 2) if total_cost else 0.0

    return {
        "holdings": summary_holdings,
        "total_value": round(total_value, 2),
        "total_cost": round(total_cost, 2),
        "total_gain": total_gain,
        "total_gain_pct": total_gain_pct,
        "accounts": accounts,
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


def parse_wealthsimple_csv(file_content: str) -> list[dict]:
    """Parse a Wealthsimple activities export CSV into transaction records.

    Wealthsimple activity CSVs have columns:
    transaction_date, settlement_date, account_id, account_type,
    activity_type, activity_sub_type, direction, symbol, name,
    currency, quantity, unit_price, commission, net_cash_amount

    We extract Buy, Sell, and SecurityTransfer activities.
    MoneyMovement (deposits, withdrawals, transfers) are skipped.

    The CSV may have a trailing timestamp line like:
    "As of 2026-02-21 19:00 GMT-05:00"

    Args:
        file_content: Raw CSV file content as a string.

    Returns:
        List of parsed transaction dicts ready for import.
    """
    # Filter out trailing non-CSV lines (e.g., "As of ..." timestamp)
    lines = file_content.strip().split("\n")
    csv_lines = []
    for line in lines:
        stripped = line.strip().strip('"')
        if stripped.lower().startswith("as of "):
            continue
        if not stripped:
            continue
        csv_lines.append(line)

    cleaned_content = "\n".join(csv_lines)
    reader = csv.DictReader(io.StringIO(cleaned_content))

    # Normalize column headers (strip whitespace, lowercase)
    if reader.fieldnames:
        reader.fieldnames = [h.strip().lower() for h in reader.fieldnames]

    # Activity types we care about and how they map
    buy_types = {"buy", "purchase"}
    sell_types = {"sell", "sale"}
    transfer_types = {"securitytransfer"}

    transactions = []
    for row in reader:
        activity_type = row.get("activity_type", "").strip().lower()

        # Determine transaction type
        if activity_type in buy_types:
            tx_type = "BUY"
        elif activity_type in sell_types:
            tx_type = "SELL"
        elif activity_type in transfer_types:
            tx_type = "TRANSFER_IN"
        else:
            # Skip money movements, dividends, fees, etc.
            continue

        symbol = row.get("symbol", "").strip().upper()
        if not symbol:
            continue

        # Parse quantity
        try:
            quantity = abs(float(row.get("quantity", "0").strip().replace(",", "")))
        except (ValueError, AttributeError):
            continue

        if quantity <= 0.0001:
            continue

        # Parse unit price
        try:
            unit_price_str = row.get("unit_price", "0").strip().replace(",", "").replace("$", "")
            unit_price = abs(float(unit_price_str)) if unit_price_str else 0.0
        except (ValueError, AttributeError):
            unit_price = 0.0

        # For SecurityTransfers, unit_price may be empty — derive from net_cash_amount
        if unit_price == 0.0:
            try:
                net_cash = abs(float(row.get("net_cash_amount", "0").strip().replace(",", "").replace("$", "")))
                unit_price = round(net_cash / quantity, 4) if quantity > 0 else 0.0
            except (ValueError, AttributeError):
                unit_price = 0.0

        # Account type
        account_type = row.get("account_type", "").strip()
        if not account_type:
            account_type = "Unspecified"
        # Normalize common values
        acct_lower = account_type.lower()
        if "non" in acct_lower and "reg" in acct_lower:
            account_type = "Non-registered"

        # Currency
        currency = row.get("currency", "CAD").strip().upper()

        # Parse date
        date_str = row.get("transaction_date", "").strip()
        try:
            tx_date = datetime.strptime(date_str, "%Y-%m-%d").isoformat()
        except ValueError:
            tx_date = datetime.now().isoformat()

        # Name
        name = row.get("name", "").strip()

        # Resolve CDR (CAD Hedged) tickers to their NEO exchange equivalents.
        # On Wealthsimple, CDRs like "Nvidia CDR (CAD Hedged)" use bare symbols
        # (NVDA, AMD, etc.) but actually trade on NEO at very different CAD prices.
        name_lower = name.lower()
        if ("cdr" in name_lower or "cad hedged" in name_lower or "cad-hedged" in name_lower):
            if "." not in symbol:
                symbol = f"{symbol}.NE"

        # Commission
        try:
            commission = abs(float(row.get("commission", "0").strip().replace(",", "").replace("$", "") or "0"))
        except (ValueError, AttributeError):
            commission = 0.0

        transactions.append({
            "ticker": symbol,
            "type": tx_type,
            "shares": round(quantity, 6),
            "price": round(unit_price, 4),
            "total": round(quantity * unit_price, 2),
            "date": tx_date,
            "account_type": account_type,
            "currency": currency,
            "name": name,
            "commission": commission,
        })

    return transactions


def import_transactions(transactions: list[dict], clear_existing: bool = False) -> dict:
    """Import a list of parsed transactions into the portfolio.

    Rebuilds holdings from scratch based on all transactions,
    keyed by (ticker, account_type).

    Args:
        transactions: List of transaction dicts from parse_wealthsimple_csv.
        clear_existing: If True, replace existing data. If False, append.

    Returns:
        Summary of the import (counts, tickers affected).
    """
    portfolio = _load_portfolio()
    portfolio = _migrate_portfolio(portfolio)

    if clear_existing:
        portfolio = {"holdings": {}, "transactions": []}

    portfolio["transactions"].extend(transactions)

    # Rebuild holdings from all transactions
    holdings_map: dict[str, dict] = {}  # key -> {shares, total_cost, account_type}
    for tx in portfolio["transactions"]:
        ticker = tx["ticker"]
        shares = tx["shares"]
        price = tx["price"]
        account_type = tx.get("account_type", "Unspecified")
        key = _holding_key(ticker, account_type)

        if key not in holdings_map:
            holdings_map[key] = {"shares": 0, "total_cost": 0.0, "account_type": account_type}

        if tx["type"] in ("BUY", "TRANSFER_IN", "IMPORT"):
            holdings_map[key]["total_cost"] += shares * price
            holdings_map[key]["shares"] += shares
        elif tx["type"] == "SELL":
            holdings_map[key]["shares"] -= shares
            # Reduce cost basis proportionally
            if holdings_map[key]["shares"] > 0:
                avg = holdings_map[key]["total_cost"] / (holdings_map[key]["shares"] + shares)
                holdings_map[key]["total_cost"] = avg * holdings_map[key]["shares"]
            else:
                holdings_map[key]["total_cost"] = 0.0

    # Convert to portfolio format, drop positions with 0 or negative shares
    portfolio["holdings"] = {}
    tickers_imported = set()
    for key, data in holdings_map.items():
        if data["shares"] > 0.0001:
            avg_price = round(data["total_cost"] / data["shares"], 4) if data["shares"] else 0
            portfolio["holdings"][key] = {
                "shares": round(data["shares"], 6),
                "avg_price": avg_price,
                "account_type": data["account_type"],
            }
            ticker, _ = _parse_holding_key(key)
            tickers_imported.add(ticker)

    _save_portfolio(portfolio)

    return {
        "transactions_imported": len(transactions),
        "tickers": sorted(tickers_imported),
        "total_holdings": len(portfolio["holdings"]),
    }
