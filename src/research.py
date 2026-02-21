"""AI research module using OpenAI for market analysis and portfolio suggestions."""

from datetime import datetime

from openai import OpenAI

from src.config import OPENAI_API_KEY, OPENAI_MODEL
from src.market_data import get_stock_price
from src.portfolio import get_portfolio_summary


def _get_client() -> OpenAI:
    """Get an OpenAI client instance.

    Returns:
        Configured OpenAI client.

    Raises:
        RuntimeError: If API key is not configured.
    """
    if not OPENAI_API_KEY:
        raise RuntimeError(
            "OpenAI API key not configured. Set OPENAI_API_KEY in your .env file."
        )
    return OpenAI(api_key=OPENAI_API_KEY)


def _build_portfolio_context() -> str:
    """Build a text summary of the current portfolio for AI prompts.

    Returns:
        Formatted string describing current holdings.
    """
    summary = get_portfolio_summary()
    if not summary["holdings"]:
        return "The portfolio is currently empty."

    lines = [
        f"Portfolio total value: ${summary['total_value']:,.2f}",
        f"Total cost basis: ${summary['total_cost']:,.2f}",
        f"Total gain/loss: ${summary['total_gain']:,.2f} ({summary['total_gain_pct']:+.2f}%)",
        "",
        "Current holdings:",
    ]
    for h in summary["holdings"]:
        lines.append(
            f"  - {h['ticker']}: {h['shares']} shares @ avg ${h['avg_price']:.2f}, "
            f"current ${h['current_price']:.2f}, "
            f"gain: ${h['gain']:,.2f} ({h['gain_pct']:+.2f}%)"
        )

    return "\n".join(lines)


def get_market_research(tickers: list[str]) -> str:
    """Get AI-generated market research for a list of tickers.

    Args:
        tickers: List of stock/ETF ticker symbols to research.

    Returns:
        Markdown-formatted market research summary.
    """
    client = _get_client()

    # Gather current price data for context
    price_context = []
    for ticker in tickers:
        try:
            data = get_stock_price(ticker)
            price_context.append(
                f"- {data['name']} ({data['ticker']}): ${data['price']:.2f}, "
                f"change: {data['change_pct']:+.2f}%, "
                f"P/E: {data.get('pe_ratio', 'N/A')}, "
                f"Market Cap: {data.get('market_cap', 'N/A')}"
            )
        except RuntimeError:
            price_context.append(f"- {ticker}: Unable to fetch current data")

    today = datetime.now().strftime("%B %d, %Y")

    response = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a knowledgeable financial analyst. Provide concise, "
                    "actionable market research. Use markdown formatting. "
                    "Include relevant recent news, sector trends, and key metrics. "
                    "Always include a disclaimer that this is not financial advice."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Today is {today}. Provide a market research briefing for "
                    f"the following stocks/ETFs:\n\n"
                    f"{''.join(price_context)}\n\n"
                    f"For each, cover:\n"
                    f"1. Recent performance and key drivers\n"
                    f"2. Notable news or upcoming events\n"
                    f"3. Sector/industry outlook\n"
                    f"4. Key risks to watch\n"
                ),
            },
        ],
        temperature=0.7,
        max_tokens=2000,
    )

    return response.choices[0].message.content


def get_portfolio_suggestions() -> str:
    """Get AI-generated suggestions for portfolio optimization.

    Returns:
        Markdown-formatted portfolio suggestions.
    """
    client = _get_client()
    portfolio_context = _build_portfolio_context()
    today = datetime.now().strftime("%B %d, %Y")

    response = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a portfolio advisor. Analyze the user's portfolio and "
                    "provide specific, actionable suggestions. Use markdown formatting. "
                    "Consider diversification, risk management, sector allocation, "
                    "and current market conditions. "
                    "Always include a disclaimer that this is not financial advice."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Today is {today}. Here is my current portfolio:\n\n"
                    f"{portfolio_context}\n\n"
                    f"Please provide:\n"
                    f"1. Portfolio health assessment (diversification, risk, allocation)\n"
                    f"2. Specific buy/sell/hold suggestions with reasoning\n"
                    f"3. Potential new positions to consider\n"
                    f"4. Risk warnings or concerns\n"
                ),
            },
        ],
        temperature=0.7,
        max_tokens=2000,
    )

    return response.choices[0].message.content


def get_daily_briefing() -> str:
    """Get a daily market briefing focused on the user's portfolio.

    Returns:
        Markdown-formatted daily briefing.
    """
    client = _get_client()
    portfolio_context = _build_portfolio_context()
    today = datetime.now().strftime("%B %d, %Y")

    response = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a financial news briefing assistant. Provide a concise "
                    "daily market briefing relevant to the user's portfolio. "
                    "Use markdown formatting. Focus on actionable information. "
                    "Always include a disclaimer that this is not financial advice."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Today is {today}. Here is my portfolio:\n\n"
                    f"{portfolio_context}\n\n"
                    f"Provide a daily briefing covering:\n"
                    f"1. Overall market conditions today\n"
                    f"2. News and events that impact my specific holdings\n"
                    f"3. Important macroeconomic developments\n"
                    f"4. Any urgent actions I should consider\n"
                ),
            },
        ],
        temperature=0.7,
        max_tokens=1500,
    )

    return response.choices[0].message.content
