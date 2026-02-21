"""Finance Bot CLI - Your personal investment assistant."""

import sys

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt

from src.market_data import get_stock_price, get_multiple_prices
from src.portfolio import add_holding, remove_holding, get_portfolio_summary, get_transactions
from src.analysis import calculate_returns, calculate_volatility, calculate_sharpe_ratio, compare_stocks
from src.utils import format_currency, format_percentage, format_large_number, validate_ticker

console = Console()


def show_banner() -> None:
    """Display the application banner."""
    console.print(
        Panel(
            "[bold cyan]📈 Finance Bot[/bold cyan]\n"
            "[dim]Your personal investment assistant[/dim]",
            border_style="cyan",
        )
    )


def show_help() -> None:
    """Display available commands."""
    table = Table(title="Available Commands", border_style="cyan")
    table.add_column("Command", style="bold green")
    table.add_column("Description")

    commands = [
        ("price <ticker>", "Get current stock price"),
        ("prices <t1> <t2> ...", "Get prices for multiple stocks"),
        ("buy <ticker> <shares> <price>", "Add a stock purchase"),
        ("sell <ticker> <shares> <price>", "Record a stock sale"),
        ("portfolio", "View portfolio summary"),
        ("history [ticker]", "View transaction history"),
        ("returns <ticker> [period]", "Calculate return metrics"),
        ("volatility <ticker> [period]", "Calculate volatility metrics"),
        ("sharpe <ticker> [period]", "Calculate Sharpe ratio"),
        ("compare <t1> <t2> ... [period]", "Compare multiple stocks"),
        ("help", "Show this help message"),
        ("quit", "Exit the application"),
    ]
    for cmd, desc in commands:
        table.add_row(cmd, desc)

    console.print(table)


def cmd_price(args: list[str]) -> None:
    """Handle the price command."""
    if not args:
        console.print("[red]Usage: price <ticker>[/red]")
        return

    ticker = validate_ticker(args[0])
    with console.status(f"Fetching price for {ticker}..."):
        data = get_stock_price(ticker)

    color = "green" if data["change"] >= 0 else "red"
    console.print(Panel(
        f"[bold]{data['name']}[/bold] ({data['ticker']})\n\n"
        f"Price: [bold]{format_currency(data['price'], data['currency'])}[/bold]\n"
        f"Change: [{color}]{format_currency(data['change'])} ({format_percentage(data['change_pct'])})[/{color}]\n"
        f"Market Cap: {format_large_number(data.get('market_cap'))}\n"
        f"P/E Ratio: {data.get('pe_ratio', 'N/A')}\n"
        f"Dividend Yield: {format_percentage(data['dividend_yield'] * 100) if data.get('dividend_yield') else 'N/A'}",
        title=f"[cyan]{ticker}[/cyan]",
        border_style="cyan",
    ))


def cmd_prices(args: list[str]) -> None:
    """Handle the prices command for multiple tickers."""
    if not args:
        console.print("[red]Usage: prices <ticker1> <ticker2> ...[/red]")
        return

    tickers = [validate_ticker(t) for t in args]
    with console.status("Fetching prices..."):
        results = get_multiple_prices(tickers)

    table = Table(title="Stock Prices", border_style="cyan")
    table.add_column("Ticker", style="bold")
    table.add_column("Name")
    table.add_column("Price", justify="right")
    table.add_column("Change", justify="right")

    for data in results:
        if "error" in data:
            table.add_row(data["ticker"], "[red]Error[/red]", "-", "-")
        else:
            color = "green" if data["change"] >= 0 else "red"
            table.add_row(
                data["ticker"],
                data.get("name", ""),
                format_currency(data["price"]),
                f"[{color}]{format_percentage(data['change_pct'])}[/{color}]",
            )

    console.print(table)


def cmd_buy(args: list[str]) -> None:
    """Handle the buy command."""
    if len(args) < 3:
        console.print("[red]Usage: buy <ticker> <shares> <price>[/red]")
        return

    ticker = validate_ticker(args[0])
    shares = float(args[1])
    price = float(args[2])

    result = add_holding(ticker, shares, price)
    console.print(
        f"[green]✓ Bought {shares} shares of {ticker} at {format_currency(price)}[/green]\n"
        f"  Total shares: {result['shares']} | Avg price: {format_currency(result['avg_price'])}"
    )


def cmd_sell(args: list[str]) -> None:
    """Handle the sell command."""
    if len(args) < 3:
        console.print("[red]Usage: sell <ticker> <shares> <price>[/red]")
        return

    ticker = validate_ticker(args[0])
    shares = float(args[1])
    price = float(args[2])

    result = remove_holding(ticker, shares, price)
    console.print(f"[green]✓ Sold {shares} shares of {ticker} at {format_currency(price)}[/green]")
    if result.get("message"):
        console.print(f"  {result['message']}")
    else:
        console.print(f"  Remaining: {result['shares']} shares")


def cmd_portfolio() -> None:
    """Handle the portfolio command."""
    with console.status("Loading portfolio..."):
        summary = get_portfolio_summary()

    if not summary["holdings"]:
        console.print("[yellow]Your portfolio is empty. Use 'buy' to add holdings.[/yellow]")
        return

    table = Table(title="Portfolio Summary", border_style="cyan")
    table.add_column("Ticker", style="bold")
    table.add_column("Shares", justify="right")
    table.add_column("Avg Price", justify="right")
    table.add_column("Current", justify="right")
    table.add_column("Value", justify="right")
    table.add_column("Gain/Loss", justify="right")

    for h in summary["holdings"]:
        color = "green" if h["gain"] >= 0 else "red"
        table.add_row(
            h["ticker"],
            str(h["shares"]),
            format_currency(h["avg_price"]),
            format_currency(h["current_price"]),
            format_currency(h["market_value"]),
            f"[{color}]{format_currency(h['gain'])} ({format_percentage(h['gain_pct'])})[/{color}]",
        )

    console.print(table)

    total_color = "green" if summary["total_gain"] >= 0 else "red"
    console.print(
        f"\n  Total Value: [bold]{format_currency(summary['total_value'])}[/bold]\n"
        f"  Total Cost:  {format_currency(summary['total_cost'])}\n"
        f"  Total Gain:  [{total_color}]{format_currency(summary['total_gain'])} "
        f"({format_percentage(summary['total_gain_pct'])})[/{total_color}]"
    )


def cmd_history(args: list[str]) -> None:
    """Handle the history command."""
    ticker = validate_ticker(args[0]) if args else None
    transactions = get_transactions(ticker)

    if not transactions:
        console.print("[yellow]No transactions found.[/yellow]")
        return

    table = Table(title="Transaction History", border_style="cyan")
    table.add_column("Date")
    table.add_column("Type", style="bold")
    table.add_column("Ticker")
    table.add_column("Shares", justify="right")
    table.add_column("Price", justify="right")
    table.add_column("Total", justify="right")

    for t in transactions:
        color = "green" if t["type"] == "BUY" else "red"
        table.add_row(
            t["date"][:10],
            f"[{color}]{t['type']}[/{color}]",
            t["ticker"],
            str(t["shares"]),
            format_currency(t["price"]),
            format_currency(t["total"]),
        )

    console.print(table)


def cmd_returns(args: list[str]) -> None:
    """Handle the returns command."""
    if not args:
        console.print("[red]Usage: returns <ticker> [period][/red]")
        return

    ticker = validate_ticker(args[0])
    period = args[1] if len(args) > 1 else "1y"

    with console.status(f"Analyzing returns for {ticker}..."):
        data = calculate_returns(ticker, period)

    color = "green" if data["total_return_pct"] >= 0 else "red"
    console.print(Panel(
        f"Total Return: [{color}]{format_percentage(data['total_return_pct'])}[/{color}]\n"
        f"Avg Daily Return: {format_percentage(data['avg_daily_return_pct'])}\n"
        f"Best Day: [green]{format_percentage(data['best_day_pct'])}[/green]\n"
        f"Worst Day: [red]{format_percentage(data['worst_day_pct'])}[/red]\n"
        f"Positive Days: {data['positive_days']} | Negative Days: {data['negative_days']}",
        title=f"[cyan]{ticker} Returns ({period})[/cyan]",
        border_style="cyan",
    ))


def cmd_volatility(args: list[str]) -> None:
    """Handle the volatility command."""
    if not args:
        console.print("[red]Usage: volatility <ticker> [period][/red]")
        return

    ticker = validate_ticker(args[0])
    period = args[1] if len(args) > 1 else "1y"

    with console.status(f"Analyzing volatility for {ticker}..."):
        data = calculate_volatility(ticker, period)

    console.print(Panel(
        f"Daily Volatility: {format_percentage(data['daily_volatility_pct'])}\n"
        f"Annual Volatility: {format_percentage(data['annual_volatility_pct'])}\n"
        f"Max Drawdown: [red]{format_percentage(data['max_drawdown_pct'])}[/red]",
        title=f"[cyan]{ticker} Volatility ({period})[/cyan]",
        border_style="cyan",
    ))


def cmd_sharpe(args: list[str]) -> None:
    """Handle the sharpe command."""
    if not args:
        console.print("[red]Usage: sharpe <ticker> [period][/red]")
        return

    ticker = validate_ticker(args[0])
    period = args[1] if len(args) > 1 else "1y"

    with console.status(f"Calculating Sharpe ratio for {ticker}..."):
        data = calculate_sharpe_ratio(ticker, period)

    console.print(Panel(
        f"Sharpe Ratio: [bold]{data['sharpe_ratio']}[/bold]\n"
        f"Annualized Return: {format_percentage(data['annualized_return_pct'])}\n"
        f"Annualized Volatility: {format_percentage(data['annualized_volatility_pct'])}\n"
        f"Risk-Free Rate: {format_percentage(data['risk_free_rate_pct'])}",
        title=f"[cyan]{ticker} Sharpe Ratio ({period})[/cyan]",
        border_style="cyan",
    ))


def cmd_compare(args: list[str]) -> None:
    """Handle the compare command."""
    if len(args) < 2:
        console.print("[red]Usage: compare <ticker1> <ticker2> ... [period][/red]")
        return

    # Check if last arg is a period
    periods = {"1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "max"}
    if args[-1].lower() in periods:
        period = args[-1].lower()
        tickers = [validate_ticker(t) for t in args[:-1]]
    else:
        period = "1y"
        tickers = [validate_ticker(t) for t in args]

    with console.status("Comparing stocks..."):
        results = compare_stocks(tickers, period)

    table = Table(title=f"Stock Comparison ({period})", border_style="cyan")
    table.add_column("Ticker", style="bold")
    table.add_column("Return", justify="right")
    table.add_column("Volatility", justify="right")
    table.add_column("Max Drawdown", justify="right")
    table.add_column("Sharpe", justify="right")

    for r in results:
        if "error" in r:
            table.add_row(r["ticker"], "[red]Error[/red]", "-", "-", "-")
        else:
            ret_color = "green" if r["total_return_pct"] >= 0 else "red"
            table.add_row(
                r["ticker"],
                f"[{ret_color}]{format_percentage(r['total_return_pct'])}[/{ret_color}]",
                format_percentage(r["annual_volatility_pct"]),
                f"[red]{format_percentage(r['max_drawdown_pct'])}[/red]",
                str(r["sharpe_ratio"]),
            )

    console.print(table)


def main() -> None:
    """Main entry point for the Finance Bot CLI."""
    show_banner()
    console.print("[dim]Type 'help' for available commands or 'quit' to exit.[/dim]\n")

    while True:
        try:
            user_input = Prompt.ask("[bold cyan]finance-bot[/bold cyan]").strip()
            if not user_input:
                continue

            parts = user_input.split()
            command = parts[0].lower()
            args = parts[1:]

            match command:
                case "help":
                    show_help()
                case "quit" | "exit" | "q":
                    console.print("[cyan]Goodbye! 👋[/cyan]")
                    sys.exit(0)
                case "price":
                    cmd_price(args)
                case "prices":
                    cmd_prices(args)
                case "buy":
                    cmd_buy(args)
                case "sell":
                    cmd_sell(args)
                case "portfolio":
                    cmd_portfolio()
                case "history":
                    cmd_history(args)
                case "returns":
                    cmd_returns(args)
                case "volatility":
                    cmd_volatility(args)
                case "sharpe":
                    cmd_sharpe(args)
                case "compare":
                    cmd_compare(args)
                case _:
                    console.print(f"[red]Unknown command: '{command}'. Type 'help' for options.[/red]")

        except KeyboardInterrupt:
            console.print("\n[cyan]Goodbye! 👋[/cyan]")
            sys.exit(0)
        except ValueError as e:
            console.print(f"[red]Input error: {e}[/red]")
        except RuntimeError as e:
            console.print(f"[red]Error: {e}[/red]")
        except Exception as e:
            console.print(f"[red]Unexpected error: {e}[/red]")


if __name__ == "__main__":
    main()
