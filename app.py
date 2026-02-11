import os

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.security import check_password_hash, generate_password_hash
import datetime

from helpers import apology, login_required, lookup, usd

# Configure application
app = Flask(__name__)

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/")
@login_required
def index():
    """Show portfolio of stocks"""
    user_id = session["user_id"]
    
    stocks = db.execute("SELECT symbol, symbol, price, SUM(shares) as totalShares FROM transactions WHERE user_id = ? GROUP BY symbol", user_id)
    cash = db.execute("SELECT cash FROM users WHERE id =?", user_id)[0]["cash"]

    total = cash
    
    for stock in stocks:
        total += stock["price"] * stock["totalShares"]
    
    return render_template("index.html", stocks = stocks, cash = cash, usd = usd, total=total)
    
    


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""
    if request.method == "GET":
        return render_template("buy.html")
    
    else:
        symbol = request.form.get("symbol")
        shares = int(request.form.get("shares"))
        
        if not symbol:
            return apology("Must give symbol")
        
        stock = lookup(symbol.upper())
        
        if stock == None:
            return apology("Symbol doesnt exist")
        
        if shares < 0:
            return apology("Shares not allowed")
    
        transaction_value = shares * stock["price"]
    
        user_id = session["user_id"]
        user_cash_db = db.execute("SELECT cash FROM users WHERE id = :id", id=user_id)
        user_cash = user_cash_db[0]["cash"]
    
        if user_cash < transaction_value:
            return apology("Not enough money")
        
        uptd_cash = user_cash - transaction_value
        
    
        # Update table
        db.execute("UPDATE users SET cash = ? WHERE id = ?", uptd_cash , user_id)
        
        date = datetime.datetime.now()
        
        # Insert into table
        db.execute("INSERT INTO transactions (user_id, symbol, shares, price, date) VALUES (?, ?, ?, ?, ?)", user_id, stock["symbol"], shares, stock["price"], date)
        
        flash("Bought!")
        
        return redirect("/")
        

        
@app.route("/history")
@login_required
def history():
    """Show history of transactions"""
    user_id = session["user_id"]
    transactions_db = db.execute("SELECT * FROM transactions WHERE user_id = :id", id=user_id)
    return render_template("history.html", transactions = transactions_db)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """GET stock quote."""
    if request.method == "POST":
        symbol = request.form.get("symbol").upper()
        if not symbol:
            return apology("Enter stock symbol")
            
      # Lookup the stock symbol by calling the lookup fuction and display the results  
        item = lookup(symbol)
        
      # Return apology("TODO")  
        if not item:
            return apology("Invalid stock symbol")
            
        return render_template("quoted.html", stock={
                'name': item['name'],
                'symbol': item['symbol'],
                'price': usd(item['price'])
            })
    else:
        return render_template('quote.html')
    
   

@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    if request.method == "GET":
        return render_template("register.html")
    
    else:
        username = request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")
        
        if not username:
            return apology("must provide username", 403)
        if not password:
            return apology("must provide password", 403)
        if not confirmation:
            return apology("must provide confirmation")
        if not password == confirmation:
            return apology("confirmation must match password", 403)
        
        hash = generate_password_hash(password)
        
        try:
            new_user = db.execute("INSERT INTO users (username, hash) VALUES (?, ?)", username, hash)
        except:
            return apology("Username already exists")
        
        session["user_id"] = new_user
        
        
        return redirect("/")


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""
    if request.method == "GET":
        user_id = session["user_id"]
        symbols_user = db.execute("SELECT symbol FROM transactions WHERE user_id = :id GROUP BY symbol HAVING SUM(shares) > 0", id=user_id)
        return render_template("sell.html", symbols = [row["symbol"] for row in symbols_user])
        
    else:
        symbol = request.form.get("symbol")
        shares = int(request.form.get("shares"))
        
        if not symbol:
            return apology("Must give symbol")
        
        stock = lookup(symbol.upper())
        
        if stock == None:
            return apology("Symbol doesnt exist")
        
        if shares < 0:
            return apology("Shares not allowed")
            
    
        transaction_value = shares * stock["price"]
    
        user_id = session["user_id"]
        user_cash_db = db.execute("SELECT cash FROM users WHERE id = :id", id=user_id)
        user_cash = user_cash_db[0]["cash"]
    
        user_shares = db.execute("SELECT shares FROM transactions WHERE user_id=:id AND symbol = :symbol GROUP BY symbol", id=user_id, symbol=symbol)
        user_shares_real = user_shares[0]["shares"]
        
        if shares > user_shares_real:
            return apology("You don't have this amount of shares!")
        
        uptd_cash = user_cash + transaction_value
    
        # Update table
        db.execute("UPDATE users SET cash = ? WHERE id = ?", uptd_cash, user_id)
        
        date = datetime.datetime.now()
        
        # Insert into table
        db.execute("INSERT INTO transactions (user_id, symbol, shares, price, date) VALUES (?, ?, ?, ?, ?)", user_id, stock["symbol"], (-1) *shares, stock["price"], date)
        
        flash("Sold!")
        
        return redirect("/")        
