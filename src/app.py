"""Flask web application for Finance Bot."""

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import markdown

from src.config import SECRET_KEY, DEBUG
from src.market_data import get_stock_price, get_stock_detail, get_multiple_prices
from src.portfolio import (
    add_holding,
    remove_holding,
    get_portfolio_summary,
    get_transactions,
    parse_wealthsimple_csv,
    import_transactions,
    ACCOUNT_TYPES,
)
from src.analysis import (
    calculate_returns,
    calculate_volatility,
    calculate_sharpe_ratio,
)
from src.research import get_market_research, get_portfolio_suggestions, get_daily_briefing

app = Flask(
    __name__,
    template_folder="../templates",
    static_folder="../static",
)
app.secret_key = SECRET_KEY


# ── Dashboard ────────────────────────────────────────────────────────────────

@app.route("/")
def dashboard():
    """Render the main dashboard with portfolio overview."""
    try:
        summary = get_portfolio_summary()
    except Exception as e:
        summary = {"holdings": [], "total_value": 0, "total_cost": 0, "total_gain": 0, "total_gain_pct": 0}
        flash(f"Error loading portfolio: {e}", "error")

    return render_template("dashboard.html", summary=summary)


# ── Portfolio Management ─────────────────────────────────────────────────────

@app.route("/portfolio/add", methods=["GET", "POST"])
def portfolio_add():
    """Add a new holding to the portfolio."""
    if request.method == "POST":
        ticker = request.form.get("ticker", "").strip().upper()
        account_type = request.form.get("account_type", "Unspecified").strip()
        try:
            shares = float(request.form.get("shares", 0))
            price = float(request.form.get("price", 0))
        except ValueError:
            flash("Shares and price must be valid numbers.", "error")
            return render_template("portfolio_add.html", account_types=ACCOUNT_TYPES)

        if not ticker or shares <= 0 or price <= 0:
            flash("Please provide a valid ticker, shares, and price.", "error")
            return render_template("portfolio_add.html", account_types=ACCOUNT_TYPES)

        try:
            result = add_holding(ticker, shares, price, account_type=account_type)
            flash(
                f"Added {shares} shares of {ticker} at ${price:.2f} in {account_type}.",
                "success",
            )
            return redirect(url_for("dashboard"))
        except Exception as e:
            flash(f"Error adding holding: {e}", "error")

    return render_template("portfolio_add.html", account_types=ACCOUNT_TYPES)


@app.route("/portfolio/sell", methods=["GET", "POST"])
def portfolio_sell():
    """Sell shares from the portfolio."""
    if request.method == "POST":
        ticker = request.form.get("ticker", "").strip().upper()
        account_type = request.form.get("account_type", "Unspecified").strip()
        try:
            shares = float(request.form.get("shares", 0))
            price = float(request.form.get("price", 0))
        except ValueError:
            flash("Shares and price must be valid numbers.", "error")
            return render_template("portfolio_sell.html", account_types=ACCOUNT_TYPES)

        if not ticker or shares <= 0 or price <= 0:
            flash("Please provide a valid ticker, shares, and price.", "error")
            return render_template("portfolio_sell.html", account_types=ACCOUNT_TYPES)

        try:
            result = remove_holding(ticker, shares, price, account_type=account_type)
            flash(f"Sold {shares} shares of {ticker} at ${price:.2f} from {account_type}.", "success")
            return redirect(url_for("dashboard"))
        except ValueError as e:
            flash(str(e), "error")
        except Exception as e:
            flash(f"Error selling: {e}", "error")

    return render_template("portfolio_sell.html", account_types=ACCOUNT_TYPES)


@app.route("/portfolio/import", methods=["GET", "POST"])
def portfolio_import():
    """Import portfolio from Wealthsimple activities CSV."""
    if request.method == "POST":
        file = request.files.get("csv_file")
        if not file or not file.filename.endswith(".csv"):
            flash("Please upload a valid .csv file.", "error")
            return render_template("import_csv.html")

        try:
            content = file.read().decode("utf-8")
            transactions = parse_wealthsimple_csv(content)

            if not transactions:
                flash("No transactions found in the CSV. Check the file format.", "error")
                return render_template("import_csv.html")

            clear = request.form.get("clear_existing") == "true"
            result = import_transactions(transactions, clear_existing=clear)

            flash(
                f"Imported {result['transactions_imported']} transactions "
                f"across {len(result['tickers'])} tickers. "
                f"Portfolio now has {result['total_holdings']} positions.",
                "success",
            )
            return redirect(url_for("dashboard"))
        except Exception as e:
            flash(f"Error importing CSV: {e}", "error")

    return render_template("import_csv.html")


@app.route("/portfolio/history")
def portfolio_history():
    """View transaction history."""
    ticker = request.args.get("ticker")
    transactions = get_transactions(ticker)
    return render_template("history.html", transactions=transactions, filter_ticker=ticker)


# ── Stock Detail ─────────────────────────────────────────────────────────────

@app.route("/stock/<ticker>")
def stock_detail(ticker: str):
    """Render detail page for a single stock/ETF."""
    try:
        detail = get_stock_detail(ticker)
        returns = calculate_returns(ticker, period="1y")
        volatility = calculate_volatility(ticker, period="1y")
        sharpe = calculate_sharpe_ratio(ticker, period="1y")
    except RuntimeError as e:
        flash(f"Error loading data for {ticker.upper()}: {e}", "error")
        return redirect(url_for("dashboard"))

    return render_template(
        "stock_detail.html",
        stock=detail,
        returns=returns,
        volatility=volatility,
        sharpe=sharpe,
    )


# ── AI Research ──────────────────────────────────────────────────────────────

@app.route("/research")
def research():
    """Render the AI research page."""
    return render_template("research.html")


@app.route("/api/research/briefing", methods=["POST"])
def api_daily_briefing():
    """API endpoint: get daily market briefing."""
    try:
        result = get_daily_briefing()
        html = markdown.markdown(result, extensions=["tables", "fenced_code"])
        return jsonify({"success": True, "content": html})
    except RuntimeError as e:
        return jsonify({"success": False, "error": str(e)}), 400
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/research/market", methods=["POST"])
def api_market_research():
    """API endpoint: get market research for specific tickers."""
    data = request.get_json()
    tickers = data.get("tickers", [])
    if not tickers:
        return jsonify({"success": False, "error": "No tickers provided."}), 400

    try:
        result = get_market_research(tickers)
        html = markdown.markdown(result, extensions=["tables", "fenced_code"])
        return jsonify({"success": True, "content": html})
    except RuntimeError as e:
        return jsonify({"success": False, "error": str(e)}), 400
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/research/suggestions", methods=["POST"])
def api_suggestions():
    """API endpoint: get portfolio suggestions."""
    try:
        result = get_portfolio_suggestions()
        html = markdown.markdown(result, extensions=["tables", "fenced_code"])
        return jsonify({"success": True, "content": html})
    except RuntimeError as e:
        return jsonify({"success": False, "error": str(e)}), 400
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ── API helpers ──────────────────────────────────────────────────────────────

@app.route("/api/price/<ticker>")
def api_price(ticker: str):
    """API endpoint: get current price for a ticker."""
    try:
        data = get_stock_price(ticker)
        return jsonify({"success": True, "data": data})
    except RuntimeError as e:
        return jsonify({"success": False, "error": str(e)}), 400


# ── Template filters ─────────────────────────────────────────────────────────

@app.template_filter("currency")
def currency_filter(value):
    """Jinja filter to format currency."""
    if value is None:
        return "N/A"
    return f"${value:,.2f}"


@app.template_filter("pct")
def pct_filter(value):
    """Jinja filter to format percentage."""
    if value is None:
        return "N/A"
    prefix = "+" if value > 0 else ""
    return f"{prefix}{value:.2f}%"


@app.template_filter("large_number")
def large_number_filter(value):
    """Jinja filter to format large numbers."""
    if value is None:
        return "N/A"
    abs_val = abs(value)
    sign = "-" if value < 0 else ""
    if abs_val >= 1e12:
        return f"{sign}{abs_val / 1e12:.2f}T"
    elif abs_val >= 1e9:
        return f"{sign}{abs_val / 1e9:.2f}B"
    elif abs_val >= 1e6:
        return f"{sign}{abs_val / 1e6:.2f}M"
    elif abs_val >= 1e3:
        return f"{sign}{abs_val / 1e3:.2f}K"
    return f"{sign}{abs_val:.2f}"
