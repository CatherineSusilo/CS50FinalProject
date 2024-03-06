import os
from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session, g
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
from functools import wraps
import hashlib
import re

app = Flask(__name__)
# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure SQLite database connect and cursor
db = SQL("sqlite:///ticketing.db")

# Buying tickets dictionary

ticketDetails = {
    "first_name": " ",
    "last_name": " ",
    "email": " ",
    "phone_number": " ",
    "birthday": " ",
    "ticket_amount": "",
    "ticket_category": " ",
    "showing": " "

}

@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

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

def apology(message, code=400):
    """Render message as an apology to user."""

    def escape(s):
        """
        Escape special characters.

        https://github.com/jacebrowning/memegen#special-characters
        """
        for old, new in [
            ("-", "--"),
            (" ", "-"),
            ("_", "__"),
            ("?", "~q"),
            ("%", "~p"),
            ("#", "~h"),
            ("/", "~s"),
            ('"', "''"),
        ]:
            s = s.replace(old, new)
        return s

    return render_template("apology.html", top=code, bottom=escape(message)), code


@app.route('/')
@login_required
def dashboard():

    return render_template('dashboard.html')

if __name__ == '__main__':
    app.run(debug=True)

@app.route('/login', methods=['GET', 'POST'])
def login():
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
        if len(rows) != 1:
            return apology("invalid username and/or password", 403)
        if not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid password", 403)
        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]
        session["position"] = rows[0]["position"]  # Assuming the position column exists in the users table

        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")

@app.route('/register', methods=['GET', 'POST'])
def register():
    session.clear()
    if request.method == "POST":
        if not request.form.get("username"):
            return apology("must provide username", 400)
        elif not request.form.get("email"):
            return apology("must provide email", 400)
        elif not request.form.get("phone"):
            return apology("must provide phone", 400)
        elif not request.form.get("password", 400):
            return apology("must provide password", 400)
        elif not request.form.get("confirm_password"):
            return apology("must confirm password", 400)
        elif request.form.get("password") != request.form.get("confirm_password"):
            return apology("passwords do not match", 400)
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))
        if len(rows) != 0:
            return apology("username already exists", 400)
        db.execute("INSERT INTO users (username, hash, email, phoneNo, checkedIn, position) VALUES(?, ?, ?, ?, ?, ?)", request.form.get("username"), generate_password_hash(request.form.get("password")), request.form.get("email"), request.form.get("phone"), 0, "customer")
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))
        session["user_id"] = rows[0]["id"]
        return redirect("/")
    else:
        return render_template("register.html")

@app.route('/login', methods=['GET', 'POST'])
def login_page():
    return render_template('login.html')

@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


def storeDetails(ticket_details):
    db.execute('''INSERT INTO ticketDetails (first_name, last_name, email, phone_number, birthday, ticket_amount, ticket_category, showing)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                (ticket_details["first_name"], ticket_details["last_name"], ticket_details["email"],
                 ticket_details["phone_number"], ticket_details["birthday"], ticket_details["ticket_amount"],
                 ticket_details["ticket_category"], ticket_details["showing"]))

def retrieveDetails():
    row = db.execute("SELECT * FROM ticketDetails ORDER BY id DESC LIMIT 1")
    if row:
        return {
            "first_name": row[1],
            "last_name": row[2],
            "email": row[3],
            "phone_number": row[4],
            "birthday": row[5],
            "ticket_amount": row[6],
            "ticket_category": row[7],
            "showing": row[8]
        }
    else:
        return None


@app.route('/buytickets', methods=['GET', 'POST'])
@login_required
def buy_tickets():
    if request.method == 'POST':
        if not request.form.get("first_name"):
            return apology("must provide first name", 400)
        elif not request.form.get("last_name"):
            return apology("must provide last name", 400)
        elif not request.form.get("email"):
            return apology("must provide email", 400)
        elif not request.form.get("phone_number"):
            return apology("must provide phone number", 400)
        elif not request.form.get("birthday"):
            return apology("must provide birthday", 400)
        elif not int(request.form['ticket_amount']):
            return apology("must provide ticket numbers", 400)
        elif not request.form.get('ticket_category'):
            return apology("must provide category", 400)
        elif not request.form.get('showing'):
            return apology("must provide showing", 400)
        # ticket_amount = int(request.form['ticket_amount'])
        ticketDetails['first_name'] = request.form.get("first_name")
        ticketDetails['last_name'] = request.form.get("last_name")
        ticketDetails['email'] = request.form.get("email")
        ticketDetails['phone_number'] = request.form.get("phone_number")
        ticketDetails['birthday'] = request.form.get("birthday")
        ticketDetails['ticket_amount'] = int(request.form['ticket_amount'])
        ticketDetails['ticket_category'] = request.form.get('ticket_category')
        ticketDetails['showing'] = request.form.get('showing')
        storeDetails(ticketDetails)

        # Redirect to the seat selection page
        return redirect('/payment')

    return render_template('buytickets.html')

@app.route('/payment', methods=['GET', 'POST'])
@login_required
def payment():
    if request.method == 'POST':
        return redirect('/payment')
    ticket_category = ticketDetails['ticket_category']
    showing = ticketDetails['showing']
    ticket_amount = ticketDetails['ticket_amount']

    # if request.method == 'POST':
    #     # Process payment logic here
    #     return redirect('/')
    # Calculate the price based on the selected ticket category and showing type
    price = 0
    if ticket_category == 'CAT1':
        price = 125000.00 if showing == 'matinee' else 150000.00
    elif ticket_category == 'CAT2':
        price = 175000.00 if showing == 'matinee' else 200000.00
    elif ticket_category == 'CAT3':
        price = 225000.00 if showing == 'matinee' else 250000.00
    elif ticket_category == 'CAT4':
        price = 275000.00 if showing == 'matinee' else 300000.00
    elif ticket_category == 'CAT5':
        price = 325000.00 if showing == 'matinee' else 350000.00

    return render_template('payment.html', first_name=ticketDetails['first_name'], ticket_category=ticket_category, showing=showing, price=price, ticket_amount=ticket_amount)

@app.route('/profile')
@login_required
def profile():
    # Retrieve user information from the database or session
    id = session.get("user_id")
    rows = db.execute("SELECT * FROM users WHERE id = ?", id)
    username = rows[0]["username"]
    email = rows[0]["email"]
    position = rows[0]["position"]
    phoneNo = rows[0]["phoneNo"]
    return render_template('profile.html', username=username, email=email, position=position, phoneNo=phoneNo)

@app.route('/database')
@login_required
def database():
    rows = db.execute("SELECT * FROM users")
    return render_template('database.html', rows=rows)


@app.route('/seatingSummary')
@login_required
def seatingSummary():
    return render_template('seatingSummary.html')

@app.route('/salesSummary')
@login_required
def salesSummary():
    return render_template('salesSummary.html')

@app.route('/editOrders')
@login_required
def editOrders():
    return render_template('editOrders.html')

@app.route('/scanTickets')
@login_required
def scanTickets():
    return render_template('scanTickets.html')
