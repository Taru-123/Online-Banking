from flask import Flask, render_template, request, redirect, url_for, session, flash
import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "change-this-secret-key"


def get_db():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="12345",
        database="online_banking"
    )


@app.route("/")
def home():
    return redirect(url_for("login"))


@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        phone = request.form["phone"]
        account_number = request.form["account_number"]
        password = request.form["password"]

        hashed_password = generate_password_hash(password)

        db = get_db()
        cursor = db.cursor()

        try:
            cursor.execute("""
                INSERT INTO users
                (name, email, phone, account_number, password)
                VALUES (%s, %s, %s, %s, %s)
            """, (
                name,
                email,
                phone,
                account_number,
                hashed_password
            ))

            db.commit()
            flash("Registration successful. Please login.")

        except mysql.connector.Error as e:
            db.rollback()
            flash("Email or account number already exists.")

        finally:
            cursor.close()
            db.close()

        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        db = get_db()
        cursor = db.cursor(dictionary=True)

        cursor.execute(
            "SELECT * FROM users WHERE email = %s",
            (email,)
        )

        user = cursor.fetchone()

        cursor.close()
        db.close()

        if user and check_password_hash(user["password"], password):

            session["user_id"] = user["id"]
            session["user_name"] = user["name"]

            return redirect(url_for("dashboard"))

        flash("Invalid email or password.")

    return render_template("login.html")


@app.route("/dashboard")
def dashboard():

    if "user_id" not in session:
        return redirect(url_for("login"))

    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute(
        "SELECT * FROM users WHERE id = %s",
        (session["user_id"],)
    )

    user = cursor.fetchone()

    cursor.execute("""
        SELECT *
        FROM transactions
        WHERE sender_id = %s OR receiver_id = %s
        ORDER BY created_at DESC
        LIMIT 5
    """, (
        session["user_id"],
        session["user_id"]
    ))

    transactions = cursor.fetchall()

    cursor.close()
    db.close()

    return render_template(
        "dashboard.html",
        user=user,
        transactions=transactions
    )


@app.route("/logout")
def logout():

    session.clear()

    return redirect(url_for("login"))


if __name__ == "__main__":
    app.run(debug=True)