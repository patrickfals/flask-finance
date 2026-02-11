import csv
import datetime
import pytz
import requests
import subprocess
import urllib
import uuid

from flask import redirect, render_template, session
from functools import wraps


def apology(message, code=400):
    """Render message as an apology to user."""
    def escape(s):
        """
        Escape special characters.

        https://github.com/jacebrowning/memegen#special-characters
        """
        for old, new in [("-", "--"), (" ", "-"), ("_", "__"), ("?", "~q"),
                         ("%", "~p"), ("#", "~h"), ("/", "~s"), ("\"", "''")]:
            s = s.replace(old, new)
        return s
    return render_template("apology.html", top=code, bottom=escape(message)), code


def login_required(f):
    """
    Decorate routes to require login.

    http://flask.pocoo.org/docs/0.12/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function


def lookup(symbol):
    """Look up quote for symbol."""

    symbol = symbol.upper().strip()
    if not symbol:
        return None

    # 1) Try Yahoo (JSON quote endpoint)
    try:
        r = requests.get(
            "https://query1.finance.yahoo.com/v7/finance/quote",
            params={"symbols": symbol},
            headers={"User-Agent": "Mozilla/5.0", "Accept": "application/json"},
            timeout=10
        )

        # If Yahoo rate-limits you, fall back (don’t even try parsing)
        if r.status_code != 429:
            r.raise_for_status()
            data = r.json()
            results = data.get("quoteResponse", {}).get("result", [])
            if results:
                q = results[0]
                price = q.get("regularMarketPrice")
                if price is not None:
                    name = q.get("shortName") or q.get("longName") or symbol
                    return {"name": name, "price": round(float(price), 2), "symbol": symbol}

    except (requests.RequestException, ValueError, KeyError, IndexError):
        pass

    # 2) Fallback: Stooq (no key). Works for many US tickers with ".US"
    try:
        stooq_symbol = symbol.lower()
        if "." not in stooq_symbol:
            stooq_symbol = f"{stooq_symbol}.us"

        stooq_url = "https://stooq.com/q/l/"
        r2 = requests.get(
            stooq_url,
            params={"s": stooq_symbol, "f": "sd2t2ohlcv", "h": "", "e": "csv"},
            headers={"User-Agent": "Mozilla/5.0", "Accept": "text/csv"},
            timeout=10
        )
        r2.raise_for_status()

        lines = r2.text.strip().splitlines()
        # Expect header + 1 data line
        if len(lines) < 2:
            return None

        row = next(csv.DictReader(lines))
        # Stooq uses "Close" column
        close = row.get("Close")
        if not close or close == "N/A":
            return None

        return {"name": symbol, "price": round(float(close), 2), "symbol": symbol}

    except (requests.RequestException, ValueError, KeyError, IndexError):
        return None



def usd(value):
    """Format value as USD."""
    return f"${value:,.2f}"
