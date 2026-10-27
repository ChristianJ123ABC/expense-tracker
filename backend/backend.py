#Sources:

#Validation
#Email Regex: #https://www.zerobounce.net/email-guides/python-email-verification

#User Authentication
#https://www.geeksforgeeks.org/python/login-and-registration-project-using-flask-and-mysql/
#https://stackoverflow.com/questions/59380641/how-to-display-full_name-in-multiple-pages-using-flask
#https://stackoverflow.com/questions/37227780/flask-session-persisting-after-close-browser

#CRUD
#https://www.freecodecamp.org/news/build-smart-expense-tracker-with-python-and-llms/
#https://medium.com/@chayasonidurg/building-a-smart-personal-expense-tracker-using-python-cd1b25fe6249
#Finding current month and the next: https://stackoverflow.com/questions/37396329/finding-first-day-of-the-month-in-python
#Converting text into money / decimal https://stackoverflow.com/questions/3887469/python-how-to-convert-currency-to-decimal
#https://www.youtube.com/watch?v=xzUpX6eiOiQ


#API / REST
#Flask Documentation: https://flask.palletsprojects.com/en/stable/api/
#https://www.geeksforgeeks.org/python/use-jsonify-instead-of-json-dumps-in-flask/
#https://flask.palletsprojects.com/en/stable/patterns/javascript/
#https://wittgeo.medium.com/building-an-expense-tracker-with-python-and-javascript-9276a9f7ba4c
#CRUD Exercise Week 12 Moodle (Deployment) https://github.com/ChristianJ123ABC/crud

import os, random, werkzeug, gunicorn, re, datetime, calendar, logging
from datetime import date, datetime
from flask import Flask, render_template, redirect, url_for, request, session, flash, jsonify
from flask_mysqldb import MySQL 
from datetime import timedelta
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash, check_password_hash
from decimal import Decimal

load_dotenv(override=True)

#Creates base directory to join to templates
directory =  os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
app = Flask(__name__, template_folder=os.path.join(directory,"frontend"), static_folder=os.path.join(directory,"frontend/static"))


app.config["MYSQL_HOST"] = os.environ["MYSQL_HOST"]
app.config["MYSQL_USER"] = os.environ["MYSQL_USER"]
app.config["MYSQL_PASSWORD"] = os.environ["MYSQL_PASSWORD"]
app.config["MYSQL_DB"] = os.environ["MYSQL_DB"]
app.config["MYSQL_PORT"] = int(os.environ.get("MYSQL_PORT"))
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
app.config["MYSQL_CHARSET"] = "utf8mb4"
app.config["SECRET_KEY"] = os.environ["SECRET_KEY"]
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(minutes=15)
CURRENCY = "EUR" #base currency (NOTE: change in library.py)
mysql = MySQL(app)

@app.route("/")
def home():
    if "user_id" in session:
        return redirect(url_for("dashboard"))
    else:
        return render_template("home.html")

@app.route("/test")
def test():
    return "Test"


@app.route("/database-check")
def database_check():
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT 1")
    cursor.close()
    return "Database Work"

# - - - - - - - - 
#  FUNCTIONS FOR VALIDATIONS / FEATURES
# - - - - - - - - 
# # #
# Input / Form Validations
# # #
#Format: mail@domain.com / firstname.surname@domain.co.uk
def isEmailValid(email):
    return re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email)

def emailExists(email):
     cursor = mysql.connection.cursor()
     cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
     user = cursor.fetchone()
     cursor.close()
     return user


# # #
# EXPENSE TRACKER FUNCTIONS
# # #


#Checks if money is in a decimal format (e.g. 50.45)
def validAmount(text):
    amount = Decimal(text).quantize(Decimal("0.01"))
    if amount <= 0 or amount > Decimal ("1000000000.00"): #Maximum: 1 billion
        return None

    return amount

def validDate(text):
    return datetime.strptime(text, "%Y-%m-%d").date()

def categoryBelongsToUser(categoryId,userId):
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT id FROM categories WHERE id = %s AND user_id = %s", (categoryId, userId))
    category = cursor.fetchone()
    cursor.close()
    return category

def categoryExists(userId, name, categoryType):
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT id FROM categories WHERE user_id = %s AND name = %s AND type = %s", (userId, name, categoryType))
    category = cursor.fetchone()
    cursor.close()
    return category


#adds up the current month's income / expenses for the user
def monthTotal(userId, categoryType):
    today = date.today()
    firstDay = today.replace(day=1)
    lastDay = today.replace(day=calendar.monthrange(today.year, today.month)[1]) #monthrange()[1] = number of days in the month

    cursor = mysql.connection.cursor()

    #Join Categories and Transactions table to get the category_id and it's type (income or expense)
    cursor.execute("SELECT SUM(t.amount_base) AS total FROM transactions t JOIN categories c ON c.id = t.category_id  "
                   "WHERE t.user_id = %s AND c.type = %s AND t.transaction_date BETWEEN %s AND %s", 
                   (userId, categoryType, firstDay, lastDay))
    
    row = cursor.fetchone()
    cursor.close()
    return row["total"] or 0 #0 is for no rows available

#Turns a month into the first and last day of that month
def monthRange(text):
    firstDay = datetime.strptime(text, "%Y-%m").date()
    if firstDay is None:
        return None

    lastDay = firstDay.replace(day=calendar.monthrange(firstDay.year, firstDay.month)[1])
    return firstDay, lastDay







# - - - - - - - - 
# FUNCTIONALITY OF THE PROJECT 
# - - - - - - - - 


# # #
#       USER AUTHENTICATION (Register, Login, Logout)
# # #
@app.route("/register", methods=["GET", "POST"])
def register():
    
    if "user_id" in session:
        flash("Please log out to register a new account.", "alert-warning")
        return redirect(url_for("dashboard"))

    elif request.method == "GET":
        return render_template("register.html")

    else:
        email = request.form["email"]
        password = request.form["password"]
        hashPass = generate_password_hash(password)

        #Input Validation
        if emailExists(email) or not isEmailValid(email):
            flash("Invalid email format: (mail@domain.com / name.surname@domain.co.uk)", "danger") 
            return render_template("register.html")

        elif len(password) < 8 or len(password) > 30:
            flash("Invalid length: use between 8 and 30 characters")
            return render_template("register.html")

        else:
            cursor = mysql.connection.cursor()
            cursor.execute("INSERT into users (email, password_hash) VALUES (%s, %s)", (email, hashPass))
            mysql.connection.commit()

            flash("Account Created.", "alert-success")
            return render_template("login.html")

@app.route("/login", methods=["GET","POST"])
def login():
    if "user_id" in session:
        flash("You are already logged in", "warning")
        return redirect(url_for("dashboard"))

    if request.method == "GET":
        return render_template("login.html")

    else:
        email = request.form["email"]
        password = request.form["password"]

        cursor = mysql.connection.cursor()
        cursor.execute("SELECT id, email, password_hash FROM users where email = %s", (email,))
        user = cursor.fetchone()
        cursor.close()

        #Validation
        if not user or not check_password_hash(user["password_hash"], password):
            flash("Invalid email address or password.", "danger")
            return render_template("login.html")

        else:
            session["user_id"] = user["id"]
            session["email"] = user["email"]
            session.permanent = True
            flash("Successfully logged in", "success")
            return redirect(url_for("dashboard"))
    

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for("login"))


# # #
#    DASHBOARD (Breakdown of this month's income, expenses and balances)
# # #
@app.route("/dashboard")
def dashboard():

    if "user_id" not in session:
        flash("Please log in to access this page.", "danger")
        return redirect(url_for("login"))

    else:
        userId = session["user_id"]
        income = monthTotal(userId, "income")
        expenses = monthTotal(userId, "expense")

        #Spending per category of the current month
        today = date.today()
        firstDay = today.replace(day=1)
        lastDay = today.replace(day=calendar.monthrange(today.year, today.month)[1])
        
        cursor = mysql.connection.cursor()

        #GROUP BY c.name places the rows into a pile per category and ORDER BY DESC lists the biggest category first
        cursor.execute("""SELECT c.name, SUM(t.amount_base) AS total FROM transactions t JOIN categories c ON c.id = t.category_id 
                       WHERE t.user_id = %s AND c.type = 'expense' AND t.transaction_date BETWEEN %s AND %s 
                       GROUP BY c.name ORDER BY total DESC""", (userId, firstDay, lastDay))
        byCategory = cursor.fetchall()
        cursor.close()

        #Passes the money variables into the dashboard to be displayed
        return render_template("dashboard.html", income=income, expenses=expenses, balance=income-expenses, by_category=byCategory, month_label=today.strftime("%B %Y"), base_currency=CURRENCY)



# # #
#     CATEGORIES (ORDER: VIEW / ADD, DELETE)
# # #
@app.route("/categories", methods=["GET", "POST"])
def categories():
    if "user_id" not in session:
        flash("You need to be logged in to see this page", "danger")
        return redirect(url_for("login"))

    userId = session["user_id"]

    if request.method == "POST":
        name = request.form["name"].strip()
        categoryType = request.form["type"]

        #Validation
        if len(name) < 3 or len(name) > 50:
            flash("Name must be between 3 and 50 characters", "danger")

        elif categoryType not in ("income", "expense"):
            flash("Invalid category: choose income or expense.", "danger")

        elif categoryExists(userId, name, categoryType):
            flash("Category already exists.", "danger")

        else:
            cursor = mysql.connection.cursor()
            cursor.execute("INSERT INTO categories (user_id, name, type) VALUES (%s, %s, %s)", (userId, name, categoryType))
            mysql.connection.commit()
            cursor.close()
            flash("Category added.", "success")

        return redirect(url_for("categories"))

    #Displays a specific user's categorys
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT id, name, type FROM categories WHERE user_id = %s ORDER BY type, name", (userId,))
    rows = cursor.fetchall()
    cursor.close()
    return render_template("categories.html", categories=rows)


@app.route("/categories/<int:category_id>/delete", methods=["POST"])
def delete_category(category_id):
    if "user_id" not in session:
        flash("Please log in to access this page.", "danger")
        return redirect(url_for("login"))

    userId = session["user_id"]

    cursor = mysql.connection.cursor()
    cursor.execute("SELECT COUNT(*) AS total FROM transactions WHERE category_id = %s AND user_id = %s", (category_id, userId))
    used = cursor.fetchone()["total"]

    if not categoryBelongsToUser(category_id, userId):
        flash("category not found", "danger")

    elif used > 0:
        flash("That category has transactions. Delete them first.", "danger")

    else:
        cursor.execute("DELETE FROM categories WHERE id = %s AND user_id = %s", (category_id, userId))
        mysql.connection.commit()
        flash("Category deleted.","success")

    cursor.close()
    return redirect(url_for("categories"))


# # #
#     TRANSACTIONS (order: VIEW/ADD, DELETE, EDIT)
# # #
@app.route("/transactions", methods = ["GET", "POST"])
def transactions():
    if "user_id" not in session:
        flash("You need to be logged in to see this page.", "danger")
        return redirect(url_for("login"))

    userId = session["user_id"]

    if request.method == "POST":
        description = request.form["description"].strip()
        categoryId = request.form["category_id"]
        amount = validAmount(request.form["amount"])
        transactionDate = validDate(request.form["transaction_date"])

        #Validation
        if amount is None or transactionDate is None:
            flash("Enter a valid amount and date.", "danger")

        elif len(description) < 1 or len(description) > 255:
            flash("Invalid description length.", "danger")

        elif not categoryBelongsToUser(categoryId, userId):
            flash("This category does not belong to you.", "danger")

        else:
            #NOTE: amount_base = amount until currency converter is implemented

            cursor = mysql.connection.cursor()
            cursor.execute("INSERT INTO transactions (user_id, category_id, description, amount, currency, amount_base, transaction_date)"
                           "VALUES (%s, %s, %s, %s, %s, %s, %s)", (userId, categoryId, description, amount, CURRENCY, amount, transactionDate))
            mysql.connection.commit()
            cursor.close()
            flash("Transaction added.", "success")

        return redirect(url_for("transactions"))

    
    cursor = mysql.connection.cursor()

    #Retrieves the 100 newest transactions that have been placed into the database per user
    #JOIN helps with giving these transactions their category name and type
    cursor.execute("""SELECT t.id, t.description, t.amount, t.currency, t.transaction_date, c.name AS category, c.type 
                    FROM transactions t JOIN categories c ON c.id = t.category_id 
                    WHERE t.user_id = %s ORDER BY t.transaction_date DESC, t.id DESC LIMIT 100""", (userId,))
    rows = cursor.fetchall()
    cursor.execute("SELECT id, name, type FROM categories WHERE user_id = %s ORDER BY type, name", (userId,))
    categoryRows = cursor.fetchall()
    cursor.close()

    #Date Format: (YYYY-MM-DD)
    return render_template("transactions.html", transactions=rows, categories=categoryRows, base_currency=CURRENCY, today=date.today().isoformat())

@app.route("/transactions/<int:transaction_id>/delete", methods=["POST"])
def delete_transaction(transaction_id):
    if "user_id" not in session:
        flash("You need to be logged in to see this page.","danger")
        return redirect(url_for("login"))

    cursor = mysql.connection.cursor()
    cursor.execute("DELETE FROM transactions WHERE id = %s AND user_id =%s", (transaction_id, session["user_id"]))
    mysql.connection.commit()

    if cursor.rowcount == 0:
        flash("Transaction not found", "danger")
    else:
        flash("Transaction deleted.", "success")

    cursor.close()
    return redirect(url_for("transactions"))


@app.route("/transactions/<int:transaction_id>/edit", methods=["GET", "POST"])
def edit_transaction(transaction_id):
    if "user_id" not in session:
        flash("You need to be logged in to see this page.", "danger")

    userId = session["user_id"]

    cursor = mysql.connection.cursor()
    cursor.execute("SELECT id, description, amount, category_id, transaction_date FROM transactions WHERE id = %s AND user_id = %s",
                   (transaction_id, userId))
    transaction = cursor.fetchone()

    if not transaction:
        cursor.close()
        flash("Transaction not found", "danger")
        return redirect(url_for("transactions"))

    if request.method == "POST":
        description = request.form["description"].strip()
        categoryId = request.form["category_id"]
        amount = validAmount(request.form["amount"])
        transactionDate = validDate(request.form["transaction_date"])

        #Validation Checks
        if amount is None or transactionDate is None:
            flash("Enter a valid amount and date", "danger")

        elif len(description) < 1 or len(description) > 255:
            flash("Invalid description length.", "danger")

        elif not categoryBelongsToUser(categoryId, userId):
            flash("This category does not belong to you", "danger")

        else:
            #NOTE: amount_base = amount until currency convert is implemented

            #Updates the user's transaction
            cursor.execute("UPDATE transactions SET category_id = %s, description = %s, amount = %s, amount_base = %s, transaction_date = %s "
                           "WHERE id = %s AND user_id = %s", (categoryId, description, amount, amount, transactionDate, transaction_id, userId))
            mysql.connection.commit()
            cursor.close()
            flash("Transaction updated.", "success")
            return redirect(url_for("transactions"))

        cursor.close()
        return redirect(url_for("edit_transaction", transaction_id = transaction_id))

    #Sends back the updated categories to the dashboard
    cursor.execute("SELECT id, name, type FROM categories WHERE user_id = %s ORDER BY type, name", (userId,))
    categoryRows = cursor.fetchall()
    cursor.close()

    return render_template("edit_transaction.html", transaction=transaction, categories=categoryRows, base_currency=CURRENCY)


# - - - - -  -
# REST API CALLS FOR TRANSACTIONS (ORDER: FUNCTIONS, POST, GET/UPDATE/DELETE)
# (GET = RECENT TRANSACTIONS, POST = ADD TRANSACTION VIA POSTMAN/CURL)
# - - - - -  -

###
# FUNCTIONS FOR VALIDATION
###


#Turns text into decimal / float (xx.xx) and the date into YYYY-MM-DD
def transactionToText(row):
    return {"id": row["id"], "category_id": row["category_id"], "category": row["category"],
            "description": row["description"], "amount": str(row["amount"]), "currency": row["currency"],
            "date": row["transaction_date"].isoformat()}


#Validation for transaction JSON
def checkTransaction(data,userId):
    if not isinstance(data, dict):
        return None, "Send as JSON"

    description = str(data.get("description", "")).strip()
    categoryId = data.get("category_id")
    amount = validAmount(str(data.get("amount", "")))
    transactionDate = validDate(str(data.get("transaction_date","")))

    if amount is None or transactionDate is None:
        return None, "Enter a valid amount + date"
    if len(description) < 1 or len(description > 255):
        return None, "Invalid description length"
    if not categoryBelongsToUser(categoryId, userId):
        return None, "This category does not belong to you"

    return (description, categoryId, amount, transactionDate), None

###
#   GET TRANSACTIONS VIA API
###
@app.route("/api/transactions", methods=["GET"])
def api_list_transactions():
    if "user_id" not in session:
        return jsonify({"error": "Login required"})

    cursor = mysql.connection.cursor()

    #Retrieves the 100 newest transactions that have been placed into the database per user
    cursor.execute("""SELECT t.id, t.category_id, t.description, t.amount, t.currency, t.transaction_date, c.name AS category
                    FROM transactions t JOIN categories c ON c.id = t.category_id
                    WHERE t.user_id = %s ORDER BY t.transaction_date DESC, t.id DESC LIMIT 100""", (session["user_id"],))
    rows = cursor.fetchall()
    cursor.close()

    return jsonify([transactionToText(row) for row in rows])

#POST: POST /api/transactions
@app.route("/api/transactions", methods=["POST"])
def api_create_transaction():
    if "user_id" not in session:
        return jsonify({"error": "Login required"}), 401

    userId = session["user_id"]
    values, error = checkTransaction(request.get_json(silent=True), userId)  #silent=True gives None instead of crashing on bad JSON

    if error:
        return jsonify({"error": error}), 400

    description, categoryId, amount, transactionDate = values

    #NOTE: amount_base = amount until currency converter is implemented
    cursor = mysql.connection.cursor()
    cursor.execute("INSERT INTO transactions (user_id, category_id, description, amount, currency, amount_base, transaction_date)"
                   "VALUES (%s, %s, %s, %s, %s, %s, %s)", (userId, categoryId, description, amount, CURRENCY, amount, transactionDate))
    mysql.connection.commit()
    newId = cursor.lastrowid
    cursor.close()

    logging.info("API: user %s created transaction %s", userId, newId)
    return jsonify({"id": newId}), 201

if __name__ == "__main__":
    app.run(debug=True, host = "0.0.0.0", port=5000)


#RETRIEVE INDIVIDUAL TRANSACTIONS:
@app.route("/api/transactions/<int:transaction_id>", methods=["GET"])
def api_get_transaction(transaction_id):
    if "user_id" not in session:
        return jsonify({"error": "Login required"}), 401

    cursor = mysql.connection.cursor()
    cursor.execute("""SELECT t.id, t.category_id, t.description, t.amount, t.currency, t.transaction_date, c.name AS category
                    FROM transactions t JOIN categories c ON c.id = t.category_id
                    WHERE t.id = %s AND t.user_id = %s""", (transaction_id, session["user_id"]))
    row = cursor.fetchone()
    cursor.close()

    if row is None:
        return jsonify({"error": "Transaction not found"}), 404

    return jsonify(transactionToText(row))