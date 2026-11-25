
from flask import Flask, request, render_template, redirect, url_for, session, flash
import sqlite3

from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

# Required for sessions
app.secret_key = "replace-with-a-long-random-secret-key"


# Database connection
def get_db():
    conn = sqlite3.connect("message.db")
    conn.row_factory = sqlite3.Row
    return conn


# Create database
def create_database():
    conn = get_db()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fullname TEXT,
            email TEXT,
            subject TEXT,
            message TEXT
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS admin (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()


create_database()


# Home
@app.route("/")
def home():
    return render_template("home.html")


# About
@app.route("/about")
def about():
    return render_template("about.html")


# Contact
@app.route("/contact", methods=["GET", "POST"])
def contact():

    if request.method == "POST":

        fullname = request.form["fullname"]
        email = request.form["email"]
        subject = request.form["subject"]
        message = request.form["message"]

        conn = get_db()

        conn.execute("""
            INSERT INTO messages
            (fullname, email, subject, message)
            VALUES (?, ?, ?, ?)
        """, (fullname, email, subject, message))

        conn.commit()
        conn.close()

        return "Message submitted successfully!"

    return render_template("contact.html")


# Create admin account
@app.route("/create-admin", methods=["GET", "POST"])
def create_admin():

    conn = get_db()

    existing_admin = conn.execute(
        "SELECT id FROM admin LIMIT 1"
    ).fetchone()

    if existing_admin:
        conn.close()
        return "Admin account already exists."

    if request.method == "POST":

        username = request.form["username"].strip()
        password = request.form["password"]

        if not username or len(password) < 12:
            conn.close()
            return "Enter a username and a password of at least 12 characters."

        hashed_password = generate_password_hash(password)

        conn.execute("""
            INSERT INTO admin (username, password)
            VALUES (?, ?)
        """, (username, hashed_password))

        conn.commit()
        conn.close()

        return redirect(url_for("login"))

    conn.close()

    return render_template("create_admin.html")


# Admin login
@app.route("/login", methods=["GET", "POST"])
def login():

    if session.get("admin_logged_in"):
        return redirect(url_for("admin"))

    if request.method == "POST":

        username = request.form["username"].strip()
        password = request.form["password"]

        conn = get_db()

        admin_user = conn.execute(
            "SELECT * FROM admin WHERE username = ?",
            (username,)
        ).fetchone()

        conn.close()

        if admin_user and check_password_hash(
            admin_user["password"], password
        ):

            session.clear()
            session["admin_logged_in"] = True
            session["admin_id"] = admin_user["id"]

            return redirect(url_for("admin"))

        flash("Invalid username or password!")

    return render_template("login.html")


# Admin dashboard
@app.route("/admin")
def admin():

    if not session.get("admin_logged_in"):
        return redirect(url_for("login"))

    conn = get_db()

    messages = conn.execute(
        "SELECT * FROM messages ORDER BY id DESC"
    ).fetchall()

    conn.close()

    return render_template("admin.html", messages=messages)


# Logout
@app.route("/logout", methods=["POST"])
def logout():

    session.clear()

    return redirect(url_for("login"))


if __name__ == "__main__":
    app.run(debug=True)
