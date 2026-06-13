# Kindred NGO — Volunteer Registration Portal

A secure, responsive, full-stack Volunteer Registration Portal built for **Kindred NGO** utilizing a Flask backend, SQLAlchemy database architecture, premium Bootstrap 5/Glassmorphic frontend styling, and robust data reporting capabilities.

Developed by **Avinash**.

---

## Key Features

- **Public Landing Page & Registration:**
  - Dynamic registration form with real-time field validation (Full Name length, email structure matching standard formatting, numeric-only phone verification, required skills checkbox array, and availability selection).
  - Submit state spinner logic displaying feedback and disabling repeat clicks on submit.
  - Micro-animated custom SVG thank-you confirmation sequence.
- **Secure Admin Panel:**
  - Session authorization using `Flask-Login` and password hashing with `Bcrypt`.
  - Comprehensive dashboard displaying volunteer statistics, texts search, and filters (skills, availability).
  - Complete inline CRUD (create, read, update, delete) operations supported by modals.
- **Data Export & Reporting:**
  - Memory-efficient streaming CSV downloads reflecting active filters.
  - Formatted PDF report generation (via ReportLab flowable elements) wrapping long fields inside professional tables.
- **Security Protections:**
  - SQL Injection prevention through parameterization (SQLAlchemy ORM).
  - Cross-Site Scripting (XSS) prevention through inputs sanitization and html escaping.

---

## Project Structure

```
/web portal
  ├── .env                   # Environment configurations (secret keys, DB paths)
  ├── .env.example           # Configurations template
  ├── app.py                 # Core application routes, filters, CRUD logic, exports
  ├── config.py              # Loads and formats configuration classes
  ├── models.py              # SQLite Database schemas (admins, volunteers)
  ├── pdf_export.py          # Custom ReportLab layout generator module
  ├── requirements.txt       # Dependencies manifest
  ├── test_app.py            # Automated Unit test suite (11 test blocks)
  ├── static/
  │    ├── css/
  │    │    └── style.css    # Branded custom styling, animations & dark theme
  │    └── js/
  │         └── validation.js # Form input validators and submit spinner logic
  └── templates/
       ├── base.html         # Shared site layout, navigation, and custom footer
       ├── register.html     # Volunteer registration form and VISION stats
       ├── success.html      # Confirmation checkmark layout
       ├── login.html        # Admin authentication card
       └── dashboard.html    # Secure administration console and modals
```

---

## Installation & Setup

### 1. Install Dependencies
Navigate to the project directory and install the required Python packages:
```bash
pip install -r requirements.txt
```

### 2. Configure Environment variables
Create a `.env` file in the root directory (based on `.env.example`):
```ini
SECRET_KEY=your_secure_random_session_key
DATABASE_URL=sqlite:///database.db
FLASK_ENV=development
FLASK_DEBUG=True
```

### 3. Launch Flask Server
Start the local server:
```bash
python app.py
```
*Note: During startup, if no database tables are found, they will automatically be initialized, and a default administrator account will be seeded:*
- **Username:** `admin`
- **Password:** `admin_pass_change_me`

### 4. Create Custom Admin Accounts
To seed a custom administrative user, execute the CLI utility command:
```bash
flask seed-admin
```
Follow the console prompts to supply the username and password.

---

## Verification & Testing

Verify that all backend endpoints, authentication redirects, sanitizations, and export streams operate correctly by running the unit test suite:
```bash
python test_app.py
```
**Test coverage details:**
- Authenticated session checks & route exclusions.
- Public registration constraints & duplicate email validation.
- XSS prevention (asserts inputs with `<script>` tags are sanitarily escaped).
- Filtering, editing, and deleting records (CRUD).
- CSV and PDF file export validation.
