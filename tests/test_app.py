import unittest
from main import app, db
from main import User, Task

class AppTests(unittest.TestCase):
    def setUp(self):
        """Set up a temporary test environment."""
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'  # In-memory database
        self.client = app.test_client()
        with app.app_context():
            db.create_all()

    def tearDown(self):
        """Clean up the test environment."""
        with app.app_context():
            db.session.remove()
            db.drop_all()

    def test_user_registration(self):
        """Test user registration functionality."""
        # Disable CSRF for testing
        app.config['WTF_CSRF_ENABLED'] = False

        response = self.client.post('/register', data={
            'email': 'test@example.com',
            'password': 'password123',
            'name': 'Test User'
        }, follow_redirects=True)

        # Check response status code
        self.assertEqual(response.status_code, 200)

        # Check if the user was added to the database
        with app.app_context():
            user = User.query.filter_by(email='test@example.com').first()
            print(user)  # Debugging: Ensure user is found
            self.assertIsNotNone(user)

    def test_task_creation(self):
        """Test task creation functionality."""
        with app.app_context():
            user = User(email='test@example.com', password='password123', name='Test User')
            db.session.add(user)
            db.session.commit()
        self.client.post('/login', data={
            'email': 'test@example.com',
            'password': 'password123'
        }, follow_redirects=True)
        response = self.client.post('/task/new', data={
            'title': 'Test Task',
            'description': 'Test Description',
            'due_date': '2025-12-31',
            'priority': 'High'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)

if __name__ == '__main__':
    unittest.main()
