# pip install -r requirements.txt
from pathlib import Path
import sqlite3

from flask import Flask, flash, redirect, render_template, request, url_for


app = Flask(__name__)
app.secret_key = "dev-secret-key"
BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "app.db"


def get_db_connection():
	connection = sqlite3.connect(DB_PATH)
	connection.row_factory = sqlite3.Row
	return connection


def init_db():
	with get_db_connection() as connection:
		connection.execute(
			"""
			CREATE TABLE IF NOT EXISTS entries (
				id INTEGER PRIMARY KEY AUTOINCREMENT,
				name TEXT NOT NULL,
				email TEXT NOT NULL,
				message TEXT NOT NULL,
				created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
			)
			"""
		)
		connection.commit()


@app.route("/", methods=["GET", "POST"])
def index():
	init_db()
	message = None
	form = {"name": "", "email": "", "message": ""}

	if request.method == "POST":
		name = request.form.get("name", "").strip()
		email = request.form.get("email", "").strip()
		message_text = request.form.get("message", "").strip()

		if name and email and message_text:
			with get_db_connection() as connection:
				connection.execute(
					"INSERT INTO entries (name, email, message) VALUES (?, ?, ?)",
					(name, email, message_text),
				)
				connection.commit()
			flash("Saved successfully.")
			return redirect(url_for("index"))

		form = {"name": name, "email": email, "message": message_text}
		message = "Please fill out all fields."

	with get_db_connection() as connection:
		entries = connection.execute(
			"SELECT name, email, message, created_at FROM entries ORDER BY id DESC"
		).fetchall()

	return render_template("index.html", entries=entries, form=form, message=message)


if __name__ == "__main__":
	init_db()
	app.run(debug=True)
