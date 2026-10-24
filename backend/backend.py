#Sources:

#Validation
#Email Regex: #https://www.zerobounce.net/email-guides/python-email-verification

#User Authentication
#https://www.geeksforgeeks.org/python/login-and-registration-project-using-flask-and-mysql/
#https://stackoverflow.com/questions/59380641/how-to-display-full_name-in-multiple-pages-using-flask
#https://stackoverflow.com/questions/37227780/flask-session-persisting-after-close-browser

import os, random, werkzeug, gunicorn, re 
from flask import Flask, render_template, redirect, url_for, request, session, flash 
from flask_mysqldb import MySQL 
from datetime import timedelta
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash, check_password_hash

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

mysql = MySQL(app)

@app.route("/test")
def test():
    return "Test"


@app.route("/database-check")
def database_check():
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT 1")
    cursor.close()
    return "Database Work"

#Input / Form Validations

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
#       HOME PAGE 
# # #
@app.route("/")
def home():
    return render_template("home.html")



# # #
#       USER AUTHENTICATION (Register, Login)
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

# # #
#          DASHBOARD
# # #
@app.route("/dashboard")
def dashboard():

    if "user_id" not in session:
        flash("Please log in to access this page.", "danger")
        return redirect(url_for("login"))

    else:
      return render_template("dashboard.html")

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run(debug=True, host = "0.0.0.0", port=5000)