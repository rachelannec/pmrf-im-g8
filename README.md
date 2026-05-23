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
├── requirements.txt            # Python dependencies list
├── templates/                  # Jinja2 HTML templates
│   ├── base.html               # Shared page layout with sidebar navigation
│   ├── landing.html            # Landing / portal selection page
│   ├── philhealth_form.html    # Main PhilHealth registration form
│   ├── member_login.html       # Member login page
│   ├── member_amendment.html   # Logged-in member details amendment portal
│   ├── admin_login.html        # Admin portal login page
│   ├── admin_dashboard.html    # Admin analytics and metrics dashboard
│   ├── admin_manage.html       # Admin panel to edit/delete members & dependents
│   └── admin_workbench.html    # Interactive SQL execution panel
├── static/                     # Static assets (CSS, JS, Images)
│   ├── css/
│   │   ├── style.css           # Global site styling
│   │   └── philhealth.css      # PhilHealth form and dashboard styling
│   ├── js/
│   │   ├── formatters.js       # Shared utility for input formatting & validations
│   │   └── philhealth_form.js  # Registration form submission and UI logic
│   └── images/
│       ├── prism_logo.png      # Portal logo branding
│       └── prism_bg.png        # Topographic map site background
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
