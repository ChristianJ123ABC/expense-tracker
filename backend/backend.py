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

import os, random, werkzeug, gunicorn, re, datetime
from datetime import date
from flask import Flask, render_template, redirect, url_for, request, session, flash 
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
CURRENCY = "EUR" #base currency (NOTE: change in library.py)
mysql = MySQL(app)

@app.route("/")
def home():
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
    amount = Decimal(text).quantize(Decimal(0.01))
    if amount <= 0 or amount > Decimal ("999999999.99"):
        return None

    return amount

def validDate(text):
    return datetime.strptime(text, "%m-%d-%Y").date()

def categoryBelongsToUser(categoryId,userId):
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT id FROM categories WHERE id = %s AND user_id = %s", (categoryId, userId))
    category = cursor.fetchone()
    cursor.close()
    return category

def categoryExists(userId, name, categoryType):
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT id FROm categories WHERE user_id = %s AND name = %s AND type = %s", (userId, name, categoryType))
    category = cursor.fetchone()
    cursor.close()
    return category

#adds up the current month's income / expenses for the user
def monthTotal(userId, categoryType):
    today = date.today()
    firstDay = today.replace(day=1)
    lastDay = today.replace(day=calendar.monthrange(today.year, today.month)[1])

    cursor = mysql.connection.cursor()
    cursor.execute("SELECT SUM(t.amount_base) AS total FROM transactions t JOIN categories c ON c.id = t.category_id  "
                   "WHERE t.user_id = %s AND c.type = %s AND t.transaction_date BETWEEN %s AND %s", 
                   (userId, categoryType, firstDay, lastDay))
    row = cursor.fetchone()
    cursor.close()
    return row["total"] or 0









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

        if not user or not check_password_hash(user["password_hash"], password):
            flash("Invalid email address or password.", "danger")
            return render_template("login.html")

        else:
            session["user_id"] = user["id"]
            session["email"] = user["email"]
            session.permament = True
            flash("Successfully logged in.", "success")
            return redirect(url_for("dashboard"))
    

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for("login"))


# # #
#          DASHBOARD (Breakdown of this month's income, expenses and balances)
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
        cursor.execute("SELECT c.name, SUM(t.amount_base) AS total FROM transactions t JOIN categories c ON c.id = t.category_id "
                       "WHERE t.user_id = %s AND c.type = 'expense' AND t.transaction_date BETWEEN %s AND %s "
                       "GROUP BY c.name ORDER BY total DESC", (userId, firstDay, lastDay))
        byCategory = cursor.fetchall()
        cursor.close()

        return render_template("dashboard.html", income=income, expenses=expenses, balance=income-expenses, by_category=byCategory, month_label=today.strftime("%B %Y"), base_currency=CURRENCY)




if __name__ == "__main__":
    app.run(debug=True, host = "0.0.0.0", port=5000)