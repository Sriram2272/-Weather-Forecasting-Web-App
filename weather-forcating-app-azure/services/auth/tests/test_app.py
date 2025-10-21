import unittest
from unittest.mock import patch
import json
import sys
import os

# Add the parent directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app, db, User

class AuthServiceTests(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['JWT_SECRET_KEY'] = 'test-secret-key'
        self.client = app.test_client()
        with app.app_context():
            db.create_all()
    
    def tearDown(self):
        with app.app_context():
            db.session.remove()
            db.drop_all()
    
    def test_health_endpoint(self):
        response = self.client.get('/health')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'healthy')
    
    def test_register_user(self):
        # Test user registration
        response = self.client.post('/api/auth/register', 
                                    json={
                                        'username': 'testuser',
                                        'email': 'test@example.com',
                                        'password': 'Password123!'
                                    })
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.data)
        self.assertEqual(data['message'], 'User registered successfully')
        
        # Verify user was created in the database
        with app.app_context():
            user = User.query.filter_by(username='testuser').first()
            self.assertIsNotNone(user)
            self.assertEqual(user.email, 'test@example.com')
    
    def test_register_duplicate_user(self):
        # Create a user first
        with app.app_context():
            user = User(username='testuser', email='test@example.com')
            user.set_password('Password123!')
            db.session.add(user)
            db.session.commit()
        
        # Try to register the same user again
        response = self.client.post('/api/auth/register', 
                                    json={
                                        'username': 'testuser',
                                        'email': 'test@example.com',
                                        'password': 'Password123!'
                                    })
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn('already exists', data['error'])
    
    def test_login_user(self):
        # Create a user first
        with app.app_context():
            user = User(username='testuser', email='test@example.com')
            user.set_password('Password123!')
            db.session.add(user)
            db.session.commit()
        
        # Test login
        response = self.client.post('/api/auth/login', 
                                    json={
                                        'username': 'testuser',
                                        'password': 'Password123!'
                                    })
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('access_token', data)
    
    def test_login_invalid_credentials(self):
        # Create a user first
        with app.app_context():
            user = User(username='testuser', email='test@example.com')
            user.set_password('Password123!')
            db.session.add(user)
            db.session.commit()
        
        # Test login with wrong password
        response = self.client.post('/api/auth/login', 
                                    json={
                                        'username': 'testuser',
                                        'password': 'WrongPassword123!'
                                    })
        self.assertEqual(response.status_code, 401)
        data = json.loads(response.data)
        self.assertIn('Invalid credentials', data['error'])
    
    def test_get_user_info(self):
        # Create a user first
        with app.app_context():
            user = User(username='testuser', email='test@example.com')
            user.set_password('Password123!')
            db.session.add(user)
            db.session.commit()
        
        # Login to get token
        login_response = self.client.post('/api/auth/login', 
                                        json={
                                            'username': 'testuser',
                                            'password': 'Password123!'
                                        })
        token = json.loads(login_response.data)['access_token']
        
        # Test getting user info
        response = self.client.get('/api/auth/user', 
                                headers={'Authorization': f'Bearer {token}'})
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['username'], 'testuser')
        self.assertEqual(data['email'], 'test@example.com')
    
    def test_validate_token(self):
        # Create a user first
        with app.app_context():
            user = User(username='testuser', email='test@example.com')
            user.set_password('Password123!')
            db.session.add(user)
            db.session.commit()
        
        # Login to get token
        login_response = self.client.post('/api/auth/login', 
                                        json={
                                            'username': 'testuser',
                                            'password': 'Password123!'
                                        })
        token = json.loads(login_response.data)['access_token']
        
        # Test token validation
        response = self.client.post('/api/auth/validate', 
                                    headers={'Authorization': f'Bearer {token}'})
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['valid'])
        self.assertEqual(data['username'], 'testuser')

if __name__ == '__main__':
    unittest.main()