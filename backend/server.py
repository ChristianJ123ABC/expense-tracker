import os
from flask import Flask, render_template, redirect, url_for, request, session, flash 
from flask_mysqldb import MySQL 

app = Flask(__name__, template_folder='templates')


app.config["MYSQL_HOST"] = os.environ["MYSQL_HOST"]
app.config["MYSQL_USER"] = os.environ["MYSQL_USER"]
app.config["MYSQL_PASSWORD"] = os.environ["MYSQL_PASSWORD"]
app.config["MYSQL_DB"] = os.environ["MYSQL_DB"]
app.config["MYSQL_PORT"] = int(os.environ.get("MYSQL_PORT", 3306))
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
app.config["MYSQL_CHARSET"] = "utf8mb4" #ALWAYS USE: Used to make files compatible when comparing to existing ones. (existingFile function)
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


