# pip install -r requirements.txt
import os
from pathlib import Path
import random
import sqlite3
from functools import wraps
import json

from flask import Flask, flash, redirect, render_template, request, session, url_for, jsonify
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)
app.secret_key = "dev-secret-key"
BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "philhealth.db"

# lets use .env file instead of hardcoding ung credentials sa code, will update the vercel settings para magamit sa deployed version
def load_env_file(env_path):
	if not env_path.exists():
		return

	for line in env_path.read_text(encoding="utf-8").splitlines():
		entry = line.strip()
		if not entry or entry.startswith("#") or "=" not in entry:
			continue

		key, value = entry.split("=", 1)
		key = key.strip()
		value = value.strip().strip('"').strip("'")
		if key and key not in os.environ:
			os.environ[key] = value


load_env_file(BASE_DIR / ".env")


def parse_admin_credentials():
	raw_credentials = os.environ.get("ADMIN_CREDENTIALS", "").strip()
	admins = {}

	for pair in raw_credentials.split(","):
		entry = pair.strip()
		if not entry or ":" not in entry:
			continue
		username, password = entry.split(":", 1)
		username = username.strip()
		password = password.strip()
		if username:
			admins[username] = password

	return {"admin": admins}


DEMO_CREDENTIALS = parse_admin_credentials()


def get_db_connection():
	connection = sqlite3.connect(DB_PATH)
	connection.row_factory = sqlite3.Row
	# ensure foreign key constraints are enforced
	connection.execute("PRAGMA foreign_keys = ON;")
	return connection


def ensure_column_exists(connection, table_name, column_name, column_definition):
	existing_columns = {
		row[1]
		for row in connection.execute(f"PRAGMA table_info({table_name})").fetchall()
	}
	if column_name not in existing_columns:
		connection.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_definition}")


def init_db():
	with get_db_connection() as connection:
		# table: registrant_details 
		connection.execute(
			"""
			CREATE TABLE IF NOT EXISTS registrant_details (
				id INTEGER PRIMARY KEY AUTOINCREMENT,
				PIN CHAR(14) NOT NULL UNIQUE,
				MemberName VARCHAR(80) NOT NULL,
				MotherMaidenName VARCHAR(80) NOT NULL,
				SpouseName VARCHAR(80),
				BirthDate DATE NOT NULL,
				BirthPlace VARCHAR(50) NOT NULL,
				Sex VARCHAR(6) NOT NULL,
				CivilStatus VARCHAR(17) NOT NULL,
				Citizenship VARCHAR(16) NOT NULL,
				PhilSysID CHAR(16) UNIQUE,
				TIN CHAR(12) UNIQUE,
				PermanentAddress VARCHAR(150) NOT NULL,
				MailingAddress VARCHAR(150) NOT NULL,
				HomePhone VARCHAR(20),
				MobilePhone VARCHAR(16) NOT NULL,
				BusinessLine VARCHAR(20),
				EmailAddress VARCHAR(100) NOT NULL,
				MemberPasswordHash TEXT,
				MemberTypeID CHAR(4) NOT NULL,
				created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
			)
			"""
		)
		# table: dependent_details (dependents linked to registrant PIN)
		connection.execute(
			"""
			CREATE TABLE IF NOT EXISTS dependent_details (
				DependentID INTEGER PRIMARY KEY AUTOINCREMENT,
				PIN CHAR(14) NOT NULL,
				DependentName VARCHAR(80) NOT NULL,
				Relationship VARCHAR(15) NOT NULL,
				DependentBirthDate DATE NOT NULL,
				DependentCitizenship VARCHAR(16) NOT NULL,
				DependentPWD VARCHAR(3) NOT NULL DEFAULT 'No',
				created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
				FOREIGN KEY (PIN) REFERENCES registrant_details(PIN)
			)
			"""
		)
		# table: membership_details (member type lookup)
		connection.execute(
			"""
			CREATE TABLE IF NOT EXISTS membership_details (
				MemberTypeID CHAR(4) PRIMARY KEY,
				MemberType VARCHAR(45) NOT NULL
			)
			"""
		)
		ensure_column_exists(connection, "registrant_details", "MemberPasswordHash", "MemberPasswordHash TEXT")
		connection.commit()


def generate_pin(connection):
	while True:
		pin = f"PH-{random.randint(0, 999_999_999):09d}-{random.randint(0, 9)}"
		row = connection.execute(
			"SELECT 1 FROM registrant_details WHERE PIN = ?",
			(pin,),
		).fetchone()
		if row is None:
			return pin


def admin_required(view_func):
	@wraps(view_func)
	def wrapped_view(*args, **kwargs):
		if not session.get("admin_user"):
			if request.is_json or request.path.endswith("/execute") or request.headers.get("X-Requested-With") == "fetch":
				return jsonify({"ok": False, "message": "Admin session expired. Please sign in again."}), 401
			return redirect(url_for("admin_login"))
		return view_func(*args, **kwargs)

	return wrapped_view


def get_admin_dashboard_data():
	with get_db_connection() as conn:
		registrant_count = conn.execute("SELECT COUNT(*) AS count FROM registrant_details").fetchone()["count"]
		dependent_count = conn.execute("SELECT COUNT(*) AS count FROM dependent_details").fetchone()["count"]
		membertype_count = conn.execute("SELECT COUNT(*) AS count FROM membership_details").fetchone()["count"]
		recent_registrants = conn.execute(
			"SELECT PIN, MemberName, MobilePhone, EmailAddress, MemberTypeID, created_at FROM registrant_details ORDER BY id DESC LIMIT 5"
		).fetchall()
		recent_dependents = conn.execute(
			"SELECT PIN, DependentName, Relationship, DependentBirthDate, created_at FROM dependent_details ORDER BY DependentID DESC LIMIT 5"
		).fetchall()

	return {
		"registrant_count": registrant_count,
		"dependent_count": dependent_count,
		"membertype_count": membertype_count,
		"recent_registrants": [dict(row) for row in recent_registrants],
		"recent_dependents": [dict(row) for row in recent_dependents],
	}


def get_admin_manage_data(search_query=None):
	with get_db_connection() as conn:
		registrants = []
		dependents = []

		member_types = conn.execute(
			"SELECT MemberTypeID, MemberType FROM membership_details ORDER BY MemberTypeID"
		).fetchall()

		if search_query:
			search_term = f"%{search_query.strip()}%"
			registrants = conn.execute(
				"""
				SELECT PIN, MemberName, MotherMaidenName, SpouseName, BirthDate, BirthPlace, Sex, CivilStatus, Citizenship, PhilSysID, TIN, PermanentAddress, MailingAddress, HomePhone, MobilePhone, BusinessLine, EmailAddress, MemberTypeID, created_at
				FROM registrant_details
				WHERE PIN LIKE ?
				   OR MemberName LIKE ?
				   OR MotherMaidenName LIKE ?
				   OR SpouseName LIKE ?
				   OR MobilePhone LIKE ?
				   OR EmailAddress LIKE ?
				   OR EXISTS (
					SELECT 1
					FROM dependent_details d
					WHERE d.PIN = registrant_details.PIN
					  AND (d.DependentName LIKE ? OR d.Relationship LIKE ?)
				   )
				ORDER BY id DESC
				""",
				(search_term, search_term, search_term, search_term, search_term, search_term, search_term, search_term),
			).fetchall()

			pins = [row["PIN"] for row in registrants]
			if pins:
				placeholders = ",".join(["?"] * len(pins))
				dependents = conn.execute(
					f"SELECT DependentID, PIN, DependentName, Relationship, DependentBirthDate, DependentCitizenship, DependentPWD, created_at FROM dependent_details WHERE PIN IN ({placeholders}) ORDER BY DependentID DESC",
					pins,
				).fetchall()
		dependents_by_pin = {}
		for dependent in dependents:
			dependents_by_pin.setdefault(dependent["PIN"], []).append(dict(dependent))

	return {
		"registrants": [dict(row) for row in registrants],
		"dependents_by_pin": dependents_by_pin,
		"member_types": [dict(row) for row in member_types],
		"search_query": (search_query or "").strip(),
	}


def read_admin_form_payload():
	return request.get_json(silent=True) or request.form


def is_read_only_sql(query):
	allowed_prefixes = ("select", "with", "pragma", "explain")
	return query.lstrip().lower().startswith(allowed_prefixes)


@app.route("/", methods=["GET", "POST"])
def index():
	# Render the PhilHealth membership form. The form submits to the JSON API endpoints
	init_db()
	return render_template("landing.html")


@app.route("/register")
def register():
    init_db()
    # Replace 'pmrf_form.html' with your groupmate's actual HTML filename if it's named differently (e.g., index.html)
    return render_template("philhealth_form.html")


@app.route("/login/admin", methods=["GET", "POST"])
def admin_login():
    init_db()
    if session.get("admin_user"):
        return redirect(url_for("admin_dashboard"))

    if request.method == "POST":
        payload = request.get_json(silent=True) or request.form
        username = payload.get("username", "").strip()
        password = payload.get("password", "").strip()
        
        # Verify credentials against our hardcoded demo dict
        if username in DEMO_CREDENTIALS["admin"] and DEMO_CREDENTIALS["admin"][username] == password:
            session["admin_user"] = username
            return jsonify({
                "ok": True,
                "message": "Login successful!",
                "redirect_url": url_for("admin_dashboard"),
            }), 200
        else:
            return jsonify({"ok": False, "message": "Invalid username or password."}), 401
            
    return render_template("admin_login.html")


@app.route("/admin/dashboard")
@admin_required
def admin_dashboard():
	init_db()
	return render_template(
		"admin_dashboard.html",
		admin_user=session.get("admin_user"),
		**get_admin_dashboard_data(),
	)


@app.route("/admin/manage")
@admin_required
def admin_manage():
	init_db()
	search_query = request.args.get("q", "").strip()
	return render_template(
		"admin_manage.html",
		admin_user=session.get("admin_user"),
		**get_admin_manage_data(search_query=search_query),
	)


@app.route("/admin/registrants/<pin>/update", methods=["POST"])
@admin_required
def admin_update_registrant(pin):
	init_db()
	payload = read_admin_form_payload()

	fields = {
		"MemberName": (payload.get("MemberName") or "").strip(),
		"MotherMaidenName": (payload.get("MotherMaidenName") or "").strip(),
		"SpouseName": (payload.get("SpouseName") or "").strip(),
		"BirthDate": (payload.get("BirthDate") or "").strip(),
		"BirthPlace": (payload.get("BirthPlace") or "").strip(),
		"Sex": (payload.get("Sex") or "").strip(),
		"CivilStatus": (payload.get("CivilStatus") or "").strip(),
		"Citizenship": (payload.get("Citizenship") or "").strip(),
		"PhilSysID": (payload.get("PhilSysID") or "").strip() or None,
		"TIN": (payload.get("TIN") or "").strip() or None,
		"PermanentAddress": (payload.get("PermanentAddress") or "").strip(),
		"MailingAddress": (payload.get("MailingAddress") or "").strip(),
		"HomePhone": (payload.get("HomePhone") or "").strip(),
		"MobilePhone": (payload.get("MobilePhone") or "").strip(),
		"BusinessLine": (payload.get("BusinessLine") or "").strip(),
		"EmailAddress": (payload.get("EmailAddress") or "").strip(),
		"MemberTypeID": (payload.get("MemberTypeID") or "").strip(),
	}

	required = [fields["MemberName"], fields["BirthDate"], fields["BirthPlace"], fields["Sex"], fields["CivilStatus"], fields["Citizenship"], fields["PermanentAddress"], fields["MailingAddress"], fields["MobilePhone"], fields["EmailAddress"], fields["MemberTypeID"]]
	if not all(required):
		return jsonify({"ok": False, "message": "Missing required fields."}), 400

	try:
		with get_db_connection() as conn:
			cursor = conn.execute(
				"""
				UPDATE registrant_details
				SET MemberName = ?, MotherMaidenName = ?, SpouseName = ?, BirthDate = ?, BirthPlace = ?,
					Sex = ?, CivilStatus = ?, Citizenship = ?, PhilSysID = ?, TIN = ?, PermanentAddress = ?,
					MailingAddress = ?, HomePhone = ?, MobilePhone = ?, BusinessLine = ?, EmailAddress = ?, MemberTypeID = ?
				WHERE PIN = ?
				""",
				(
					fields["MemberName"], fields["MotherMaidenName"] or "N/A", fields["SpouseName"] or None, fields["BirthDate"], fields["BirthPlace"],
					fields["Sex"], fields["CivilStatus"], fields["Citizenship"], fields["PhilSysID"], fields["TIN"], fields["PermanentAddress"],
					fields["MailingAddress"], fields["HomePhone"], fields["MobilePhone"], fields["BusinessLine"], fields["EmailAddress"], fields["MemberTypeID"], pin,
				),
			)
			conn.commit()
			if cursor.rowcount == 0:
				return jsonify({"ok": False, "message": "Registrant not found."}), 404

			# --- Dependent handling: support JSON list or form field named 'dependents' ---
			# Expecting dependents as a JSON array of objects with keys:
			# DependentID (optional), DependentName, Relationship, DependentBirthDate, DependentCitizenship, DependentPWD
			dependents_raw = payload.get("dependents") if isinstance(payload, dict) else None
			deleted_raw = payload.get("deleted_dependent_ids") if isinstance(payload, dict) else None
			dependents_list = []
			if dependents_raw:
				if isinstance(dependents_raw, str):
					try:
						dependents_list = json.loads(dependents_raw)
					except Exception:
						dependents_list = []
				elif isinstance(dependents_raw, list):
					dependents_list = dependents_raw

			# parse deleted ids
			deleted_ids = []
			if deleted_raw:
				if isinstance(deleted_raw, str):
					try:
						deleted_ids = json.loads(deleted_raw)
					except Exception:
						# comma-separated fallback
						deleted_ids = [int(x) for x in deleted_raw.split(",") if x.strip().isdigit()]
				elif isinstance(deleted_raw, list):
					deleted_ids = [int(x) for x in deleted_raw]

			# perform deletions first
			for did in deleted_ids:
				conn.execute("DELETE FROM dependent_details WHERE DependentID = ? AND PIN = ?", (did, pin))

			# upsert dependents
			for d in dependents_list:
				if not isinstance(d, dict):
					continue
				dep_id = d.get("DependentID") or d.get("DependentId") or None
				name = (d.get("DependentName") or d.get("Dependentname") or "").strip()
				rel = (d.get("Relationship") or d.get("relationship") or "").strip()
				bdate = (d.get("DependentBirthDate") or d.get("DependentBirthdate") or "").strip()
				cit = (d.get("DependentCitizenship") or d.get("DependentCitizenship") or "").strip()
				pwd = (d.get("DependentPWD") or d.get("DependentPwd") or "No").strip()

				if not all([name, rel, bdate, cit]):
					# skip incomplete dependent rows
					continue

				if dep_id:
					try:
						dep_cursor = conn.execute(
							"""
							UPDATE dependent_details
							SET PIN = ?, DependentName = ?, Relationship = ?, DependentBirthDate = ?, DependentCitizenship = ?, DependentPWD = ?
							WHERE DependentID = ?
						""",
						(pin, name, rel, bdate, cit, pwd, dep_id),
					)
						if dep_cursor.rowcount == 0:
							conn.execute(
								"INSERT INTO dependent_details (PIN, DependentName, Relationship, DependentBirthDate, DependentCitizenship, DependentPWD) VALUES (?, ?, ?, ?, ?, ?)",
								(pin, name, rel, bdate, cit, pwd),
							)
					except sqlite3.IntegrityError:
						# skip invalid dependent entries
						continue
				else:
					# insert new dependent
					try:
						conn.execute(
							"INSERT INTO dependent_details (PIN, DependentName, Relationship, DependentBirthDate, DependentCitizenship, DependentPWD) VALUES (?, ?, ?, ?, ?, ?)",
							(pin, name, rel, bdate, cit, pwd),
						)
					except sqlite3.IntegrityError:
						continue

			conn.commit()
	except sqlite3.IntegrityError as error:
		return jsonify({"ok": False, "message": str(error)}), 400

	return jsonify({"ok": True, "message": "Registrant updated."})


@app.route("/admin/registrants/<pin>/delete", methods=["POST"])
@admin_required
def admin_delete_registrant(pin):
	init_db()
	with get_db_connection() as conn:
		conn.execute("DELETE FROM dependent_details WHERE PIN = ?", (pin,))
		cursor = conn.execute("DELETE FROM registrant_details WHERE PIN = ?", (pin,))
		conn.commit()
		if cursor.rowcount == 0:
			return jsonify({"ok": False, "message": "Registrant not found."}), 404

	return jsonify({"ok": True, "message": "Registrant deleted."})


@app.route("/admin/dependents/<int:dependent_id>/update", methods=["POST"])
@admin_required
def admin_update_dependent(dependent_id):
	init_db()
	payload = read_admin_form_payload()

	pin = (payload.get("PIN") or "").strip()
	name = (payload.get("DependentName") or "").strip()
	relationship = (payload.get("Relationship") or "").strip()
	birthdate = (payload.get("DependentBirthDate") or "").strip()
	citizenship = (payload.get("DependentCitizenship") or "").strip()
	pwd = (payload.get("DependentPWD") or "No").strip()

	if not all([pin, name, relationship, birthdate, citizenship]):
		return jsonify({"ok": False, "message": "Missing required fields."}), 400

	with get_db_connection() as conn:
		cursor = conn.execute(
			"""
			UPDATE dependent_details
			SET PIN = ?, DependentName = ?, Relationship = ?, DependentBirthDate = ?, DependentCitizenship = ?, DependentPWD = ?
			WHERE DependentID = ?
			""",
			(pin, name, relationship, birthdate, citizenship, pwd, dependent_id),
		)
		conn.commit()
		if cursor.rowcount == 0:
			return jsonify({"ok": False, "message": "Dependent not found."}), 404

	return jsonify({"ok": True, "message": "Dependent updated."})


@app.route("/admin/dependents/<int:dependent_id>/delete", methods=["POST"])
@admin_required
def admin_delete_dependent(dependent_id):
	init_db()
	with get_db_connection() as conn:
		cursor = conn.execute("DELETE FROM dependent_details WHERE DependentID = ?", (dependent_id,))
		conn.commit()
		if cursor.rowcount == 0:
			return jsonify({"ok": False, "message": "Dependent not found."}), 404

	return jsonify({"ok": True, "message": "Dependent deleted."})


@app.route("/admin/workbench")
@admin_required
def admin_workbench():
	init_db()
	with get_db_connection() as conn:
		tables = conn.execute(
			"SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
		).fetchall()
	return render_template(
		"admin_workbench.html",
		admin_user=session.get("admin_user"),
		tables=[row["name"] for row in tables],
		default_query="SELECT PIN, MemberName, MobilePhone, EmailAddress, created_at FROM registrant_details ORDER BY id DESC LIMIT 25;\n\n-- To see metadata (put this on next line and remove other query and this comment): PRAGMA table_info(registrant_details);",
	)


@app.route("/admin/workbench/execute", methods=["POST"])
@admin_required
def admin_workbench_execute():
	init_db()
	payload = request.get_json(silent=True) or request.form
	query = (payload.get("query") or "").strip()

	if not query:
		return jsonify({"ok": False, "message": "Enter an SQL query."}), 400

	if not is_read_only_sql(query):
		return jsonify({"ok": False, "message": "Only read-only SQL queries are allowed in this workbench."}), 400

	try:
		with get_db_connection() as conn:
			cursor = conn.execute(query)
			columns = [description[0] for description in cursor.description] if cursor.description else []
			rows = [dict(row) for row in cursor.fetchall()] if columns else []
			return jsonify({
				"ok": True,
				"columns": columns,
				"rows": rows,
				"rowcount": len(rows),
				"message": f"Query returned {len(rows)} row(s).",
			})
	except sqlite3.Error as error:
		return jsonify({"ok": False, "message": f"SQL error: {error}"}), 400


@app.route("/admin/logout")
@admin_required
def admin_logout():
	session.pop("admin_user", None)
	return redirect(url_for("admin_login"))


@app.route("/login/member", methods=["GET", "POST"])
def member_login():
    init_db()
    if session.get("member_pin"):
        return redirect(url_for("member_amendment"))

    error_message = None
    if request.method == "POST":
        payload = request.get_json(silent=True) or request.form
        pin = (payload.get("PIN") or payload.get("pin") or "").strip()
        password = (payload.get("password") or payload.get("Password") or "").strip()

        if not pin or not password:
            error_message = "Enter both your PhilHealth ID/Email and password."
        else:
            with get_db_connection() as conn:
                member = conn.execute(
                    "SELECT PIN, MemberPasswordHash FROM registrant_details WHERE PIN = ? OR EmailAddress = ?",
                    (pin, pin),
                ).fetchone()
            
            # --- DEBUG LINES PLACED PROPERLY RIGHT AFTER SQL FETCH ---
            print("--- DEBUG LOGIN ---")
            print(f"Input PIN/Email: {pin}")
            print(f"Database Record Found: {dict(member) if member else 'NONE'}")
            if member:
                print(f"Stored Hash in DB: {member['MemberPasswordHash']}")
            # --------------------------------------------------------

            if member and member["MemberPasswordHash"] and check_password_hash(member["MemberPasswordHash"], password):
                session["member_pin"] = member["PIN"]
                return redirect(url_for("member_amendment"))
            
            error_message = "Invalid PIN or password."

    return render_template("member_login.html", error_message=error_message)


def member_required(view_func):
	@wraps(view_func)
	def wrapped_view(*args, **kwargs):
		if not session.get("member_pin"):
			return redirect(url_for("member_login"))
		return view_func(*args, **kwargs)

	return wrapped_view


@app.route("/member/logout")
def member_logout():
	session.pop("member_pin", None)
	return redirect(url_for("member_login"))


@app.route("/member/amendment", methods=["GET", "POST"])
@member_required
def member_amendment():
	init_db()
	pin = session.get("member_pin")
	message = None
	message_type = "success"

	def calculate_age(birth_date_string):
		from datetime import date, datetime

		try:
			birth_date = datetime.strptime(birth_date_string, "%Y-%m-%d").date()
		except ValueError:
			return None

		today = date.today()
		age = today.year - birth_date.year
		if (today.month, today.day) < (birth_date.month, birth_date.day):
			age -= 1
		return age

	with get_db_connection() as conn:
		member = conn.execute(
			"""
			SELECT PIN, MemberName, MotherMaidenName, SpouseName, BirthDate, BirthPlace, Sex,
			       CivilStatus, Citizenship, PhilSysID, TIN, PermanentAddress, MailingAddress,
			       HomePhone, MobilePhone, BusinessLine, EmailAddress, MemberTypeID, created_at
			FROM registrant_details
			WHERE PIN = ?
			""",
			(pin,),
		).fetchone()
		member_types = conn.execute(
			"SELECT MemberTypeID, MemberType FROM membership_details ORDER BY MemberTypeID"
		).fetchall()
		dependents = conn.execute(
			"""
			SELECT DependentID, PIN, DependentName, Relationship, DependentBirthDate, DependentCitizenship, DependentPWD, created_at
			FROM dependent_details
			WHERE PIN = ?
			ORDER BY DependentID DESC
			""",
			(pin,),
		).fetchall()

	if member is None:
		session.pop("member_pin", None)
		return redirect(url_for("member_login"))

	if request.method == "POST":
		action = (request.form.get("DependentAction") or "").strip().lower()

		if action in {"add", "update"}:
			dependent_name = (request.form.get("DependentName") or "").strip()
			relationship = (request.form.get("Relationship") or "").strip()
			dependent_birth_date = (request.form.get("DependentBirthDate") or "").strip()
			dependent_citizenship = (request.form.get("DependentCitizenship") or "").strip()
			dependent_pwd = (request.form.get("DependentPWD") or "No").strip() or "No"

			if dependent_pwd.lower() != "yes":
				if relationship.lower() == "child":
					child_age = calculate_age(dependent_birth_date)
					if child_age is None or child_age >= 21:
						message = "Child dependents must be below 21 years old (unless PWD)."
						message_type = "error"
						return render_template(
							"member_amendment.html",
							member=dict(member),
							member_types=[dict(row) for row in member_types],
							dependents=[dict(row) for row in dependents],
							message=message,
							message_type=message_type,
						)
				elif relationship.lower() == "parent":
					parent_age = calculate_age(dependent_birth_date)
					if parent_age is None or parent_age < 60:
						message = "Parent dependents must be 60 years old and above (unless PWD)."
						message_type = "error"
						return render_template(
							"member_amendment.html",
							member=dict(member),
							member_types=[dict(row) for row in member_types],
							dependents=[dict(row) for row in dependents],
							message=message,
							message_type=message_type,
						)

			if not all([dependent_name, relationship, dependent_birth_date, dependent_citizenship]):
				message = "Missing required fields for the dependent update."
				message_type = "error"
			else:
				with get_db_connection() as conn:
					if action == "add":
						conn.execute(
							"""
							INSERT INTO dependent_details (PIN, DependentName, Relationship, DependentBirthDate, DependentCitizenship, DependentPWD)
							VALUES (?, ?, ?, ?, ?, ?)
							""",
							(pin, dependent_name, relationship, dependent_birth_date, dependent_citizenship, dependent_pwd),
						)
						message = "Dependent added successfully."
					else:
						dependent_id = (request.form.get("DependentID") or "").strip()
						if not dependent_id.isdigit():
							message = "Missing dependent ID for update."
							message_type = "error"
						else:
							cursor = conn.execute(
								"""
								UPDATE dependent_details
								SET DependentName = ?, Relationship = ?, DependentBirthDate = ?, DependentCitizenship = ?, DependentPWD = ?
								WHERE DependentID = ? AND PIN = ?
								""",
								(dependent_name, relationship, dependent_birth_date, dependent_citizenship, dependent_pwd, int(dependent_id), pin),
							)
							if cursor.rowcount == 0:
								message = "Dependent record not found."
								message_type = "error"
							else:
								message = "Dependent updated successfully."

					conn.commit()

				member = conn.execute(
					"""
					SELECT PIN, MemberName, MotherMaidenName, SpouseName, BirthDate, BirthPlace, Sex,
					       CivilStatus, Citizenship, PhilSysID, TIN, PermanentAddress, MailingAddress,
					       HomePhone, MobilePhone, BusinessLine, EmailAddress, MemberTypeID, created_at
					FROM registrant_details
					WHERE PIN = ?
					""",
					(pin,),
				).fetchone()
				dependents = conn.execute(
					"""
					SELECT DependentID, PIN, DependentName, Relationship, DependentBirthDate, DependentCitizenship, DependentPWD, created_at
					FROM dependent_details
					WHERE PIN = ?
					ORDER BY DependentID DESC
					""",
					(pin,),
				).fetchall()
		elif not action:
			editable_fields = {
				"SpouseName": (request.form.get("SpouseName") or "").strip(),
				"PhilSysID": (request.form.get("PhilSysID") or "").strip() or None,
				"TIN": (request.form.get("TIN") or "").strip() or None,
				"PermanentAddress": (request.form.get("PermanentAddress") or "").strip(),
				"MailingAddress": (request.form.get("MailingAddress") or "").strip(),
				"HomePhone": (request.form.get("HomePhone") or "").strip(),
				"MobilePhone": (request.form.get("MobilePhone") or "").strip(),
				"BusinessLine": (request.form.get("BusinessLine") or "").strip(),
				"EmailAddress": (request.form.get("EmailAddress") or "").strip(),
				"CivilStatus": (request.form.get("CivilStatus") or "").strip(),
				"Citizenship": (request.form.get("Citizenship") or "").strip(),
				"MemberTypeID": (request.form.get("MemberTypeID") or "").strip(),
			}

			required = [editable_fields["PermanentAddress"], editable_fields["MailingAddress"], editable_fields["MobilePhone"], editable_fields["EmailAddress"], editable_fields["CivilStatus"], editable_fields["Citizenship"], editable_fields["MemberTypeID"]]
			if not all(required):
				message = "Missing required fields for the amendment update."
				message_type = "error"
			else:
				with get_db_connection() as conn:
					cursor = conn.execute(
						"""
						UPDATE registrant_details
						SET SpouseName = ?, PhilSysID = ?, TIN = ?, PermanentAddress = ?, MailingAddress = ?,
							HomePhone = ?, MobilePhone = ?, BusinessLine = ?, EmailAddress = ?, CivilStatus = ?,
							Citizenship = ?, MemberTypeID = ?
						WHERE PIN = ?
						""",
						(
							editable_fields["SpouseName"] or None,
							editable_fields["PhilSysID"],
							editable_fields["TIN"],
							editable_fields["PermanentAddress"],
							editable_fields["MailingAddress"],
							editable_fields["HomePhone"] or None,
							editable_fields["MobilePhone"],
							editable_fields["BusinessLine"] or None,
							editable_fields["EmailAddress"],
							editable_fields["CivilStatus"],
							editable_fields["Citizenship"],
							editable_fields["MemberTypeID"],
							pin,
						),
					)
					conn.commit()
					if cursor.rowcount == 0:
						message = "Member record not found."
						message_type = "error"
					else:
						message = "Your PhilHealth amendment details were updated."
						member = conn.execute(
							"""
							SELECT PIN, MemberName, MotherMaidenName, SpouseName, BirthDate, BirthPlace, Sex,
							       CivilStatus, Citizenship, PhilSysID, TIN, PermanentAddress, MailingAddress,
							       HomePhone, MobilePhone, BusinessLine, EmailAddress, MemberTypeID, created_at
							FROM registrant_details
							WHERE PIN = ?
							""",
							(pin,),
						).fetchone()
						dependents = conn.execute(
							"""
							SELECT DependentID, PIN, DependentName, Relationship, DependentBirthDate, DependentCitizenship, DependentPWD, created_at
							FROM dependent_details
							WHERE PIN = ?
							ORDER BY DependentID DESC
							""",
							(pin,),
						).fetchall()

	return render_template(
		"member_amendment.html",
		member=dict(member),
		member_types=[dict(row) for row in member_types],
		dependents=[dict(row) for row in dependents],
		message=message,
		message_type=message_type,
	)


@app.route("/registrants", methods=["GET", "POST"])
def registrants():
	init_db()

	if request.method == "POST":
		# accept JSON or form-encoded
		payload = request.get_json(silent=True) or request.form

		pin = (payload.get("PIN") or payload.get("pin") or "").strip()
		member_name = (payload.get("MemberName") or payload.get("membername") or "").strip()
		member_password = (payload.get("MemberPassword") or payload.get("memberpassword") or "").strip()
		mother = (payload.get("MotherMaidenName") or payload.get("mothermaidenname") or "").strip()
		spouse = (payload.get("SpouseName") or payload.get("spousename") or "").strip()
		birthdate = (payload.get("BirthDate") or payload.get("birthdate") or "").strip()
		birthplace = (payload.get("BirthPlace") or payload.get("birthplace") or "").strip()
		sex = (payload.get("Sex") or payload.get("sex") or "").strip()
		civil = (payload.get("CivilStatus") or payload.get("civilstatus") or "").strip()
		citizenship = (payload.get("Citizenship") or payload.get("citizenship") or "").strip()
		philsys = (payload.get("PhilSysID") or payload.get("philsysid") or "").strip()  or None
		tin = (payload.get("TIN") or payload.get("tin") or "").strip() or None
		perm_addr = (payload.get("PermanentAddress") or payload.get("permanentaddress") or "").strip()
		mail_addr = (payload.get("MailingAddress") or payload.get("mailingaddress") or "").strip()
		home = (payload.get("HomePhone") or payload.get("homephone") or "").strip()
		mobile = (payload.get("MobilePhone") or payload.get("mobilephone") or "").strip()
		business = (payload.get("BusinessLine") or payload.get("businessline") or "").strip()
		email = (payload.get("EmailAddress") or payload.get("emailaddress") or "").strip()
		mtype = (payload.get("MemberTypeID") or payload.get("membertypeid") or "").strip()

		required = [member_name, member_password, birthdate, birthplace, sex, civil, citizenship, perm_addr, mail_addr, mobile, email, mtype]
		if not all(required):
			return jsonify({"ok": False, "message": "Missing required fields"}), 400

		try:
			with get_db_connection() as conn:
				if not pin:
					pin = generate_pin(conn)
				if not mother:
					mother = "N/A"
				password_hash = generate_password_hash(member_password)
				conn.execute(
					"""
					INSERT INTO registrant_details (
						PIN, MemberName, MotherMaidenName, SpouseName, BirthDate, BirthPlace,
						Sex, CivilStatus, Citizenship, PhilSysID, TIN, PermanentAddress,
						MailingAddress, HomePhone, MobilePhone, BusinessLine, EmailAddress, MemberPasswordHash, MemberTypeID
					) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
					""",
					(
						pin, member_name, mother, spouse, birthdate, birthplace,
						sex, civil, citizenship, philsys, tin, perm_addr,
						mail_addr, home, mobile, business, email, password_hash, mtype,
					),
				)
				conn.commit()
		except sqlite3.IntegrityError as e:
			return jsonify({"ok": False, "message": str(e)}), 400

		return jsonify({"ok": True, "message": "Registrant saved.", "PIN": pin}), 201

	# GET: return all registrants as JSON
	with get_db_connection() as conn:
		rows = conn.execute(
			"SELECT PIN, MemberName, MotherMaidenName, SpouseName, BirthDate, BirthPlace, Sex, CivilStatus, Citizenship, PhilSysID, TIN, PermanentAddress, MailingAddress, HomePhone, MobilePhone, BusinessLine, EmailAddress, MemberTypeID, created_at FROM registrant_details ORDER BY id DESC"
		).fetchall()

	data = [dict(r) for r in rows]
	return jsonify({"ok": True, "count": len(data), "registrants": data})


@app.route("/dependents", methods=["GET", "POST"])
def dependents():
	init_db()

	if request.method == "POST":
		payload = request.get_json(silent=True) or request.form

		pin = (payload.get("PIN") or payload.get("pin") or "").strip()
		name = (payload.get("DependentName") or payload.get("dependentname") or "").strip()
		relationship = (payload.get("Relationship") or payload.get("relationship") or "").strip()
		birthdate = (payload.get("DependentBirthDate") or payload.get("dependentbirthdate") or "").strip()
		citizenship = (payload.get("DependentCitizenship") or payload.get("dependentcitizenship") or "").strip()
		pwd = (payload.get("DependentPWD") or payload.get("dependentpwd") or "No").strip()

		required = [pin, name, relationship, birthdate, citizenship]
		if not all(required):
			return jsonify({"ok": False, "message": "Missing required fields"}), 400

		try:
			with get_db_connection() as conn:
				conn.execute(
					"INSERT INTO dependent_details (PIN, DependentName, Relationship, DependentBirthDate, DependentCitizenship, DependentPWD) VALUES (?, ?, ?, ?, ?, ?)",
					(pin, name, relationship, birthdate, citizenship, pwd),
				)
				conn.commit()
		except sqlite3.IntegrityError as e:
			return jsonify({"ok": False, "message": str(e)}), 400

		return jsonify({"ok": True, "message": "Dependent saved."}), 201

	with get_db_connection() as conn:
		rows = conn.execute(
			"SELECT DependentID, PIN, DependentName, Relationship, DependentBirthDate, DependentCitizenship, DependentPWD, created_at FROM dependent_details ORDER BY DependentID DESC"
		).fetchall()

	data = [dict(r) for r in rows]
	return jsonify({"ok": True, "count": len(data), "dependents": data})


@app.route("/membertypes", methods=["GET", "POST"])
def membertypes():
	init_db()

	if request.method == "POST":
		payload = request.get_json(silent=True) or request.form

		mtid = (payload.get("MemberTypeID") or payload.get("membertypeid") or "").strip()
		mtype = (payload.get("MemberType") or payload.get("membertype") or "").strip()

		if not mtid or not mtype:
			return jsonify({"ok": False, "message": "Missing MemberTypeID or MemberType"}), 400

		try:
			with get_db_connection() as conn:
				conn.execute(
					"INSERT INTO membership_details (MemberTypeID, MemberType) VALUES (?, ?)",
					(mtid, mtype),
				)
				conn.commit()
		except sqlite3.IntegrityError as e:
			return jsonify({"ok": False, "message": str(e)}), 400

		return jsonify({"ok": True, "message": "Member type saved."}), 201

	with get_db_connection() as conn:
		rows = conn.execute(
			"SELECT MemberTypeID, MemberType FROM membership_details ORDER BY MemberTypeID"
		).fetchall()

	data = [dict(r) for r in rows]
	return jsonify({"ok": True, "count": len(data), "membertypes": data})


if __name__ == "__main__":
	init_db()
	app.run(debug=True)