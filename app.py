import os
import re
import html
import csv
import io
from datetime import datetime, timezone
from flask import Flask, render_template, request, redirect, url_for, flash, Response, send_file
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_bcrypt import Bcrypt
from models import db, Admin, Volunteer
from config import Config
from pdf_export import generate_volunteers_pdf

# Initialize application
app = Flask(__name__)
app.config.from_object(Config)

# Initialize extensions
db.init_app(app)
bcrypt = Bcrypt(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please authenticate to access the admin portal.'
login_manager.login_message_category = 'warning'


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(Admin, int(user_id))


# Setup database and seed admin if none exists
def setup_database():
    try:
        with app.app_context():
            db.create_all()
            # Seed default admin if table is empty
            if Admin.query.count() == 0:
                default_username = 'admin'
                default_pass = 'admin_pass_change_me'
                hashed_pw = bcrypt.generate_password_hash(default_pass).decode('utf-8')
                
                admin_user = Admin(username=default_username, password_hash=hashed_pw)
                db.session.add(admin_user)
                db.session.commit()
                
                print("=" * 60)
                print("WARNING: Default Admin account seeded successfully!")
                print(f"Username: {default_username}")
                print(f"Password: {default_pass}")
                print("PLEASE CHANGE THIS PASSWORD AS SOON AS YOU LOG IN!")
                print("=" * 60)
    except Exception as e:
        print(f"Database setup warning/error: {e}")

database_initialized = False

@app.before_request
def check_db_initialized():
    global database_initialized
    if not database_initialized:
        setup_database()
        database_initialized = True


# Helper validation functions
def validate_email(email):
    email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(email_regex, email))


def validate_phone(phone):
    phone_regex = r'^[0-9]{10,15}$'
    return bool(re.match(phone_regex, phone))


# Input Sanitization helper to protect against XSS
def sanitize_input(text):
    if not text:
        return ""
    # Strip leading/trailing whitespaces and escape html characters
    return html.escape(text.strip())


# Public Routes
@app.route('/')
def index():
    return redirect(url_for('register'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    # If admin is logged in, they can still view it, but we offer a signup form
    if request.method == 'POST':
        # Retrieve and sanitize form inputs
        name = sanitize_input(request.form.get('name'))
        email = sanitize_input(request.form.get('email'))
        phone = sanitize_input(request.form.get('phone'))
        selected_skills = request.form.getlist('skills')
        availability = sanitize_input(request.form.get('availability'))

        # Backend validations
        errors = []
        if not name or len(name) < 2:
            errors.append("Full Name is required (minimum 2 characters).")
        
        if not email or not validate_email(email):
            errors.append("A valid email address is required.")
            
        if not phone or not validate_phone(phone):
            errors.append("A valid numeric phone number (10 to 15 digits) is required.")
            
        if not selected_skills:
            errors.append("Please select at least one skill or interest.")
            
        if not availability or availability not in ['Weekdays', 'Weekends', 'Flexible']:
            errors.append("Please select a valid availability option.")

        if errors:
            for error in errors:
                flash(error, 'error')
            return render_template('register.html')

        # Check for unique email constraint
        existing_volunteer = Volunteer.query.filter_by(email=email).first()
        if existing_volunteer:
            flash("This email address has already been registered.", 'error')
            return render_template('register.html')

        # Combine skills list to comma-separated string
        skills_str = ", ".join([sanitize_input(skill) for skill in selected_skills])

        try:
            # Create and save Volunteer
            new_volunteer = Volunteer(
                name=name,
                email=email,
                phone=phone,
                skills=skills_str,
                availability=availability
            )
            db.session.add(new_volunteer)
            db.session.commit()
            return redirect(url_for('success'))
        except Exception as e:
            db.session.rollback()
            flash("An error occurred while saving your registration. Please try again.", 'error')
            return render_template('register.html')

    return render_template('register.html')


@app.route('/success')
def success():
    return render_template('success.html')


# Admin Authentication Routes
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = sanitize_input(request.form.get('username'))
        password = request.form.get('password') # Passwords should not be html-escaped before validation

        if not username or not password:
            flash("Please enter both username and password.", 'error')
            return render_template('login.html')

        admin = Admin.query.filter_by(username=username).first()
        if admin and bcrypt.check_password_hash(admin.password_hash, password):
            remember = True if request.form.get('remember') else False
            login_user(admin, remember=remember)
            flash("Authenticated successfully.", "success")
            return redirect(url_for('dashboard'))
        else:
            flash("Invalid username or password.", "error")

    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash("You have logged out of the portal.", "info")
    return redirect(url_for('login'))


# Protected Admin Dashboard & CRUD Routes
@app.route('/dashboard')
@login_required
def dashboard():
    search = request.args.get('search', '').strip()
    skill = request.args.get('skill', '').strip()
    availability = request.args.get('availability', '').strip()

    # Base query for volunteers
    query = Volunteer.query

    # Search filter (parameterized naturally by SQLAlchemy ORM)
    if search:
        query = query.filter(
            (Volunteer.name.ilike(f'%{search}%')) |
            (Volunteer.email.ilike(f'%{search}%')) |
            (Volunteer.phone.ilike(f'%{search}%'))
        )

    # Skill filter (since skills are comma-separated, check if substring matches)
    if skill:
        query = query.filter(Volunteer.skills.contains(skill))

    # Availability filter
    if availability:
        query = query.filter(Volunteer.availability == availability)

    # Order by registration date descending
    volunteers = query.order_by(Volunteer.registration_date.desc()).all()

    # Calculate global overview stats
    total_count = Volunteer.query.count()
    weekdays_count = Volunteer.query.filter_by(availability='Weekdays').count()
    weekends_count = Volunteer.query.filter_by(availability='Weekends').count()
    flexible_count = Volunteer.query.filter_by(availability='Flexible').count()

    return render_template(
        'dashboard.html',
        volunteers=volunteers,
        total_count=total_count,
        weekdays_count=weekdays_count,
        weekends_count=weekends_count,
        flexible_count=flexible_count
    )


@app.route('/admin/volunteer/<int:volunteer_id>/edit', methods=['POST'])
@login_required
def edit_volunteer(volunteer_id):
    volunteer = db.session.get(Volunteer, volunteer_id)
    if not volunteer:
        flash("Volunteer record not found.", "error")
        return redirect(url_for('dashboard'))

    name = sanitize_input(request.form.get('name'))
    email = sanitize_input(request.form.get('email'))
    phone = sanitize_input(request.form.get('phone'))
    selected_skills = request.form.getlist('skills')
    availability = sanitize_input(request.form.get('availability'))

    # Backend validations
    errors = []
    if not name or len(name) < 2:
        errors.append("Full Name is required (minimum 2 characters).")
    
    if not email or not validate_email(email):
        errors.append("A valid email address is required.")
        
    if not phone or not validate_phone(phone):
        errors.append("A valid numeric phone number is required.")
        
    if not selected_skills:
        errors.append("Please select at least one skill.")
        
    if not availability or availability not in ['Weekdays', 'Weekends', 'Flexible']:
        errors.append("Please select a valid availability option.")

    if errors:
        for error in errors:
            flash(error, 'error')
        return redirect(url_for('dashboard'))

    # Check for unique email excluding current record
    email_check = Volunteer.query.filter(Volunteer.email == email, Volunteer.id != volunteer_id).first()
    if email_check:
        flash("Email is already in use by another volunteer.", "error")
        return redirect(url_for('dashboard'))

    skills_str = ", ".join([sanitize_input(skill) for skill in selected_skills])

    try:
        volunteer.name = name
        volunteer.email = email
        volunteer.phone = phone
        volunteer.skills = skills_str
        volunteer.availability = availability
        
        db.session.commit()
        flash(f"Successfully updated details for {name}.", "success")
    except Exception as e:
        db.session.rollback()
        flash("An error occurred while saving updates. Please try again.", "error")

    return redirect(url_for('dashboard'))


@app.route('/admin/volunteer/<int:volunteer_id>/delete', methods=['POST'])
@login_required
def delete_volunteer(volunteer_id):
    volunteer = db.session.get(Volunteer, volunteer_id)
    if not volunteer:
        flash("Volunteer record not found.", "error")
        return redirect(url_for('dashboard'))

    try:
        name = volunteer.name
        db.session.delete(volunteer)
        db.session.commit()
        flash(f"Volunteer record for {name} has been removed.", "success")
    except Exception as e:
        db.session.rollback()
        flash("Failed to delete record. Please try again.", "error")

    return redirect(url_for('dashboard'))


# Report Generation & Export Routes
@app.route('/admin/export/csv')
@login_required
def export_csv():
    search = request.args.get('search', '').strip()
    skill = request.args.get('skill', '').strip()
    availability = request.args.get('availability', '').strip()

    # Re-apply current dashboard filters to export matching list
    query = Volunteer.query
    if search:
        query = query.filter(
            (Volunteer.name.ilike(f'%{search}%')) |
            (Volunteer.email.ilike(f'%{search}%')) |
            (Volunteer.phone.ilike(f'%{search}%'))
        )
    if skill:
        query = query.filter(Volunteer.skills.contains(skill))
    if availability:
        query = query.filter(Volunteer.availability == availability)

    volunteers = query.order_by(Volunteer.registration_date.desc()).all()

    # Stream CSV response
    def generate():
        data = io.StringIO()
        writer = csv.writer(data)
        
        # Write headers
        writer.writerow(['ID', 'Name', 'Email', 'Phone', 'Skills', 'Availability', 'Registration Date (UTC)'])
        yield data.getvalue()
        data.seek(0)
        data.truncate(0)

        for v in volunteers:
            writer.writerow([
                v.id,
                v.name,
                v.email,
                v.phone,
                v.skills,
                v.availability,
                v.registration_date.strftime('%Y-%m-%d %H:%M:%S')
            ])
            yield data.getvalue()
            data.seek(0)
            data.truncate(0)

    response = Response(generate(), mimetype='text/csv')
    timestamp = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
    response.headers.set('Content-Disposition', 'attachment', filename=f'volunteers_report_{timestamp}.csv')
    return response


@app.route('/admin/export/pdf')
@login_required
def export_pdf():
    search = request.args.get('search', '').strip()
    skill = request.args.get('skill', '').strip()
    availability = request.args.get('availability', '').strip()

    # Re-apply current dashboard filters to export matching list
    query = Volunteer.query
    if search:
        query = query.filter(
            (Volunteer.name.ilike(f'%{search}%')) |
            (Volunteer.email.ilike(f'%{search}%')) |
            (Volunteer.phone.ilike(f'%{search}%'))
        )
    if skill:
        query = query.filter(Volunteer.skills.contains(skill))
    if availability:
        query = query.filter(Volunteer.availability == availability)

    volunteers = query.order_by(Volunteer.registration_date.desc()).all()

    # Generate ReportLab document
    pdf_buffer = generate_volunteers_pdf(volunteers, search, skill, availability)
    timestamp = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')

    return send_file(
        pdf_buffer,
        as_attachment=True,
        download_name=f'volunteers_report_{timestamp}.pdf',
        mimetype='application/pdf'
    )


# Command line helper to seed custom admin users
@app.cli.command("seed-admin")
def seed_admin_cli():
    """Seeds a custom admin user from environment variables or prompts."""
    import click
    username = click.prompt("Enter admin username", type=str)
    password = click.prompt("Enter admin password", type=str, hide_input=True, confirmation_prompt=True)
    
    with app.app_context():
        existing = Admin.query.filter_by(username=username).first()
        if existing:
            click.echo("Error: Username already exists.")
            return

        hashed_pw = bcrypt.generate_password_hash(password).decode('utf-8')
        admin_user = Admin(username=username, password_hash=hashed_pw)
        db.session.add(admin_user)
        db.session.commit()
        click.echo(f"Admin user '{username}' created successfully!")


# App Entry Point
if __name__ == '__main__':
    setup_database()
    # Read port from env if set (e.g. on Render), otherwise default to 5000
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
else:
    # Running under WSGI (like Gunicorn)
    setup_database()
