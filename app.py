# pip install -r requirements.txt
import os
from pathlib import Path
import random
import sqlite3
from functools import wraps

from flask import Flask, flash, redirect, render_template, request, session, url_for, jsonify

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
			if request.is_json or request.path.endswith("/execute"):
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
		default_query="SELECT PIN, MemberName, MobilePhone, EmailAddress, created_at FROM registrant_details ORDER BY id DESC LIMIT 25;",
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


@app.route("/login/member")
def member_login():
    init_db()
    return render_template("member_login.html")


@app.route("/registrants", methods=["GET", "POST"])
def registrants():
	init_db()

	if request.method == "POST":
		# accept JSON or form-encoded
		payload = request.get_json(silent=True) or request.form

		pin = (payload.get("PIN") or payload.get("pin") or "").strip()
		member_name = (payload.get("MemberName") or payload.get("membername") or "").strip()
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

		required = [member_name, birthdate, birthplace, sex, civil, citizenship, perm_addr, mail_addr, mobile, email, mtype]
		if not all(required):
			return jsonify({"ok": False, "message": "Missing required fields"}), 400

		try:
			with get_db_connection() as conn:
				if not pin:
					pin = generate_pin(conn)
				if not mother:
					mother = "N/A"
				conn.execute(
					"""
					INSERT INTO registrant_details (
						PIN, MemberName, MotherMaidenName, SpouseName, BirthDate, BirthPlace,
						Sex, CivilStatus, Citizenship, PhilSysID, TIN, PermanentAddress,
						MailingAddress, HomePhone, MobilePhone, BusinessLine, EmailAddress, MemberTypeID
					) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
					""",
					(
						pin, member_name, mother, spouse, birthdate, birthplace,
						sex, civil, citizenship, philsys, tin, perm_addr,
						mail_addr, home, mobile, business, email, mtype,
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