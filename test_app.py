import unittest
import io
import csv
from app import app, db, bcrypt
from models import Admin, Volunteer

class VolunteerPortalTestCase(unittest.TestCase):
    def setUp(self):
        # Configure app for testing
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        
        self.client = app.test_client()
        
        # Create database and seed admin
        with app.app_context():
            db.create_all()
            
            # Seed testing admin
            self.admin_username = 'testadmin'
            self.admin_password = 'testpassword'
            hashed_pw = bcrypt.generate_password_hash(self.admin_password).decode('utf-8')
            
            admin_user = Admin(username=self.admin_username, password_hash=hashed_pw)
            db.session.add(admin_user)
            db.session.commit()
            
            # Seed a default volunteer
            v = Volunteer(
                name='Jane Doe',
                email='jane@example.com',
                phone='9876543210',
                skills='Teaching, Content Writing',
                availability='Weekends'
            )
            db.session.add(v)
            db.session.commit()

    def tearDown(self):
        with app.app_context():
            db.drop_all()

    # --- Authentication Tests ---
    def test_login_logout_flow(self):
        # Test successful login
        response = self.client.post('/login', data={
            'username': self.admin_username,
            'password': self.admin_password
        }, follow_redirects=True)
        self.assertIn(b'Admin Dashboard', response.data)
        
        # Test logout
        response = self.client.get('/logout', follow_redirects=True)
        self.assertIn(b'Portal Access', response.data)

    def test_invalid_login(self):
        # Test incorrect password
        response = self.client.post('/login', data={
            'username': self.admin_username,
            'password': 'wrongpassword'
        }, follow_redirects=True)
        self.assertIn(b'Invalid username or password', response.data)

    def test_unauthenticated_dashboard_redirect(self):
        # Attempt accessing dashboard without logging in
        response = self.client.get('/dashboard', follow_redirects=True)
        self.assertIn(b'Please authenticate to access the admin portal.', response.data)

    # --- Volunteer Registration Tests ---
    def test_successful_volunteer_registration(self):
        response = self.client.post('/register', data={
            'name': 'Bob Smith',
            'email': 'bob@smith.com',
            'phone': '1234567890',
            'skills': ['Web Development', 'Fundraising'],
            'availability': 'Flexible'
        }, follow_redirects=True)
        self.assertIn(b'Application Successfully Submitted', response.data)
        
        # Verify db insert
        with app.app_context():
            v = Volunteer.query.filter_by(email='bob@smith.com').first()
            self.assertIsNotNone(v)
            self.assertEqual(v.name, 'Bob Smith')
            self.assertEqual(v.availability, 'Flexible')
            self.assertIn('Web Development', v.skills)

    def test_duplicate_email_registration(self):
        # jane@example.com is seeded in setUp
        response = self.client.post('/register', data={
            'name': 'Duplicate Jane',
            'email': 'jane@example.com',
            'phone': '9999999999',
            'skills': ['Teaching'],
            'availability': 'Weekdays'
        }, follow_redirects=True)
        self.assertIn(b'This email address has already been registered.', response.data)

    def test_invalid_registration_fields(self):
        # Invalid email and phone format
        response = self.client.post('/register', data={
            'name': 'X',  # name too short
            'email': 'invalid-email',
            'phone': 'abc12345', # alpha characters
            'skills': [],
            'availability': 'invalid-choice'
        }, follow_redirects=True)
        self.assertIn(b'Full Name is required', response.data)
        self.assertIn(b'A valid email address is required', response.data)
        self.assertIn(b'A valid numeric phone number', response.data)
        self.assertIn(b'Please select at least one skill', response.data)

    # --- Security & XSS Protection Tests ---
    def test_xss_input_sanitization(self):
        malicious_input = '<script>alert("xss")</script>'
        response = self.client.post('/register', data={
            'name': malicious_input,
            'email': 'hacker@safe.com',
            'phone': '0000000000',
            'skills': ['Teaching'],
            'availability': 'Flexible'
        }, follow_redirects=True)
        
        # Verify db entry is html-escaped
        with app.app_context():
            v = Volunteer.query.filter_by(email='hacker@safe.com').first()
            self.assertEqual(v.name, '&lt;script&gt;alert(&quot;xss&quot;)&lt;/script&gt;')

    # --- Admin Dashboard CRUD Tests ---
    def login_admin(self):
        self.client.post('/login', data={
            'username': self.admin_username,
            'password': self.admin_password
        })

    def test_volunteer_edit_by_admin(self):
        self.login_admin()
        
        # Get Jane Doe's ID
        with app.app_context():
            jane = Volunteer.query.filter_by(email='jane@example.com').first()
            jane_id = jane.id

        # Update Jane Doe's details
        response = self.client.post(f'/admin/volunteer/{jane_id}/edit', data={
            'name': 'Jane Updated',
            'email': 'jane.updated@example.com',
            'phone': '1112223333',
            'skills': ['Teaching'],
            'availability': 'Weekdays'
        }, follow_redirects=True)
        
        self.assertIn(b'Successfully updated details for Jane Updated', response.data)
        
        with app.app_context():
            updated_jane = db.session.get(Volunteer, jane_id)
            self.assertEqual(updated_jane.name, 'Jane Updated')
            self.assertEqual(updated_jane.email, 'jane.updated@example.com')
            self.assertEqual(updated_jane.availability, 'Weekdays')

    def test_volunteer_delete_by_admin(self):
        self.login_admin()
        
        with app.app_context():
            jane = Volunteer.query.filter_by(email='jane@example.com').first()
            jane_id = jane.id

        response = self.client.post(f'/admin/volunteer/{jane_id}/delete', follow_redirects=True)
        self.assertIn(b'Volunteer record for Jane Doe has been removed', response.data)
        
        with app.app_context():
            deleted_jane = db.session.get(Volunteer, jane_id)
            self.assertIsNone(deleted_jane)

    # --- Exports Tests ---
    def test_csv_export(self):
        self.login_admin()
        
        response = self.client.get('/admin/export/csv')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, 'text/csv')
        self.assertIn(b'jane@example.com', response.data)
        
        # Read content via csv reader
        csv_data = response.data.decode('utf-8')
        f = io.StringIO(csv_data)
        reader = csv.reader(f)
        rows = list(reader)
        self.assertEqual(rows[0][1], 'Name')
        self.assertEqual(rows[1][1], 'Jane Doe')

    def test_pdf_export(self):
        self.login_admin()
        
        response = self.client.get('/admin/export/pdf')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, 'application/pdf')
        # Check PDF header bytes (PDF files start with %PDF)
        self.assertTrue(response.data.startswith(b'%PDF'))

if __name__ == '__main__':
    unittest.main()
