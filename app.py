# pip install -r requirements.txt
from pathlib import Path
import sqlite3

from flask import Flask, flash, redirect, render_template, request, url_for, jsonify


app = Flask(__name__)
app.secret_key = "dev-secret-key"
BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "philhealth.db"


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


@app.route("/", methods=["GET", "POST"])
def index():
	# Render the PhilHealth membership form. The form submits to the JSON API endpoints
	init_db()
	return render_template("philhealth_form.html")



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
		philsys = (payload.get("PhilSysID") or payload.get("philsysid") or "").strip()
		tin = (payload.get("TIN") or payload.get("tin") or "").strip()
		perm_addr = (payload.get("PermanentAddress") or payload.get("permanentaddress") or "").strip()
		mail_addr = (payload.get("MailingAddress") or payload.get("mailingaddress") or "").strip()
		home = (payload.get("HomePhone") or payload.get("homephone") or "").strip()
		mobile = (payload.get("MobilePhone") or payload.get("mobilephone") or "").strip()
		business = (payload.get("BusinessLine") or payload.get("businessline") or "").strip()
		email = (payload.get("EmailAddress") or payload.get("emailaddress") or "").strip()
		mtype = (payload.get("MemberTypeID") or payload.get("membertypeid") or "").strip()

		required = [pin, member_name, mother, birthdate, birthplace, sex, civil, citizenship, perm_addr, mail_addr, mobile, email, mtype]
		if not all(required):
			return jsonify({"ok": False, "message": "Missing required fields"}), 400

		try:
			with get_db_connection() as conn:
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

		return jsonify({"ok": True, "message": "Registrant saved."}), 201

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