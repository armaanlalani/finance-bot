# Finance Bot 📈

A web-based personal investment assistant that tracks your portfolio, fetches live market data, and uses AI to provide market research and portfolio suggestions.

## Features

- **Web Dashboard** — View your entire portfolio at a glance with live prices
- **Portfolio Tracking** — Add/sell positions with full transaction history
- **Stock/ETF Detail Pages** — Price charts, key metrics, returns, volatility, Sharpe ratio
- **AI Market Research** — OpenAI-powered daily briefings on your holdings
- **Portfolio Suggestions** — AI recommendations for buys, sells, and rebalancing
- **Ticker Research** — Deep-dive research on any stock or ETF

## Quick Start

### Prerequisites

- Python 3.10+
- An [OpenAI API key](https://platform.openai.com/api-keys) (for AI features)

### Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Set up your environment variables
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY
```

### Run the app

```bash
python run.py
```

Then open **http://localhost:5000** in your browser.

## Pages

| Page | URL | Description |
|---|---|---|
| Dashboard | `/` | Portfolio overview with all holdings |
| Add Position | `/portfolio/add` | Buy shares of a stock/ETF |
| Sell Position | `/portfolio/sell` | Sell shares from your portfolio |
| History | `/portfolio/history` | Full transaction history |
| Stock Detail | `/stock/<TICKER>` | Deep dive on any ticker |
| AI Research | `/research` | Daily briefing, suggestions, ticker research |

## AI Features

The AI Research page offers three tools (requires OpenAI API key):

1. **Daily Briefing** — Market overview tailored to your portfolio holdings
2. **Portfolio Suggestions** — Buy/sell/hold recommendations with reasoning
3. **Ticker Research** — Enter any tickers for detailed market research

## Running Tests

```bash
pytest tests/ -v
```

## Project Structure

```
finance-bot/
├── run.py               # App entry point
├── src/
│   ├── app.py           # Flask web application & routes
│   ├── config.py        # Configuration & environment variables
│   ├── market_data.py   # Yahoo Finance data fetching
│   ├── portfolio.py     # Portfolio management & tracking
│   ├── analysis.py      # Financial analysis & metrics
│   ├── research.py      # OpenAI-powered market research
│   └── utils.py         # Utility functions
├── templates/           # HTML templates (Jinja2 + Tailwind)
├── tests/               # Test suite
├── data/                # Local portfolio storage
├── .env.example         # Environment variable template
└── requirements.txt
```

## License

MIT
