# PhilHealth Membership Registration App

A small Flask + SQLite app for managing PhilHealth membership registration data.

**LIVE DEMO: https://pmrf-im.vercel.app/**

## Features

- PhilHealth registration form with auto-generated unique PINs
- Member type lookup from `membership_details`
- Registrant and dependent saving to SQLite
- JSON API endpoints for registrants, dependents, and member types

## Project Structure

```text
pmrf-im-g8/
├── app.py                      # Flask app, database setup, and API routes
├── philhealth.db               # SQLite database file for saved records
├── templates/                  # Jinja2 HTML templates
│   ├── base.html               # Shared page layout
│   └── philhealth_form.html    # Main PhilHealth registration form
├── static/                     # Static files such as CSS
│   └── css/
│       ├── style.css           # Global site styling
│       └── philhealth.css      # PhilHealth form-specific styling
├── NOTES.md                    # SQL notes and database reminders
├── README.md                   # Project overview and setup guide
└── .gitignore                  # Files ignored by Git
```



## Requirements

- Python 3
- Flask and other packages from `requirements.txt`

## Setup

Install dependencies:

```bash
pip install -r requirements.txt
```

Run the app:

```bash
python app.py
```

Open the app in your browser:

```text
http://127.0.0.1:5000
```

## Database Notes

- `membership_details` is a lookup table for member types.
- `registrant_details.MemberTypeID` stores the selected lookup key, not the description.
- The PIN is generated automatically in the form using the format `XX-XXXXXXXX-X`.

## API Endpoints

- `GET /registrants`
- `POST /registrants`
- `GET /dependents`
- `POST /dependents`
- `GET /membertypes`
- `POST /membertypes`

## What To Do Next

Suggested follow-up tasks for the project:

1. Display saved output in the UI.
	- Show submitted registrants in a table or card list below the form.
	- Include the generated PIN, member name, member type, and timestamp.

2. Improve the UI.
	- Align fields more closely with the PhilHealth form layout.
	- Make the page clearer on mobile and desktop.

3. Add light animations.
	- Fade in cards and form sections on page load.
	- Add small transitions for buttons, alerts, and dependent rows.

4. Add validation and feedback.
	- Warn the user if required fields are missing.
	- Show success and error messages in a cleaner form area.

5. Add print or export support.
	- Make the form printable.
	- Optionally add PDF export later.

## Suggestions

If you want the next best improvement, I recommend this order:

1. Show output below the form so users can confirm what was saved.
2. Polish the UI layout and spacing.
3. Add subtle animations only after the layout is stable.

