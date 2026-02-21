<!-- Workspace-specific custom instructions for GitHub Copilot -->

# Finance Bot - Copilot Instructions

## Project Overview
A web-based finance bot with AI-powered market research, portfolio tracking, and investment analysis.

## Tech Stack
- **Language:** Python 3.10+
- **Web Framework:** Flask
- **Market Data:** yfinance
- **AI Research:** OpenAI API (GPT-4o)
- **Data Analysis:** pandas, numpy
- **Frontend:** Jinja2 templates, Tailwind CSS (CDN), Chart.js
- **Testing:** pytest
- **Config:** python-dotenv (.env file)
- **Package Management:** pip with requirements.txt

## Project Structure
```
finance-bot/
├── run.py                   # App entry point
├── src/
│   ├── __init__.py
│   ├── app.py               # Flask routes & web app
│   ├── config.py            # Environment & app config
│   ├── market_data.py       # Yahoo Finance data fetching
│   ├── portfolio.py         # Portfolio management & tracking
│   ├── analysis.py          # Financial analysis & metrics
│   ├── research.py          # OpenAI market research & suggestions
│   └── utils.py             # Utility functions
├── templates/
│   ├── base.html            # Layout template
│   ├── dashboard.html       # Portfolio dashboard
│   ├── portfolio_add.html   # Add position form
│   ├── portfolio_sell.html  # Sell position form
│   ├── history.html         # Transaction history
│   ├── stock_detail.html    # Stock/ETF detail page
│   └── research.html        # AI research page
├── tests/
│   ├── test_market_data.py
│   ├── test_portfolio.py
│   └── test_analysis.py
├── data/
│   └── portfolio.json       # Local portfolio storage
├── .env.example             # Environment variable template
├── requirements.txt
└── README.md
```

## Coding Conventions
- Use type hints for all function signatures
- Follow PEP 8 style guidelines
- Write docstrings for all public functions and classes
- Use f-strings for string formatting
- Handle exceptions gracefully with informative error messages
- Flask routes return HTML via Jinja2 templates; API routes return JSON

## Key Features
- Web dashboard with portfolio overview and live prices
- Add/sell positions with transaction history
- Stock/ETF detail pages with charts and financial metrics
- AI-powered daily briefings, market research, and portfolio suggestions
- OpenAI integration for investment insights
